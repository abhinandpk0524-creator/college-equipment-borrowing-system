from smtplib import SMTPException

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from equipment.models import BorrowNotification, BorrowRequest
from equipment.notifications import (
    create_borrow_notification,
    send_borrow_notification_email,
)


class Command(BaseCommand):
    help = (
        'Send due-today and first-overdue borrower notifications. '
        'Schedule this command to run once daily.'
    )

    def handle(self, *args, **options):
        today = timezone.localdate()
        BorrowRequest.objects.filter(
            status='ISSUED',
            expected_return_date__lt=today,
        ).update(status='OVERDUE')

        due_today_requests = BorrowRequest.objects.filter(
            status='ISSUED',
            expected_return_date=today,
        ).select_related('user', 'equipment')
        overdue_requests = BorrowRequest.objects.filter(
            status='OVERDUE',
            expected_return_date__lt=today,
        ).select_related('user', 'equipment')

        created_count = 0
        for notification_type, requests in (
            ('DUE_TODAY', due_today_requests),
            ('OVERDUE', overdue_requests),
        ):
            for borrow_request in requests:
                notification, created = create_borrow_notification(
                    borrow_request,
                    notification_type,
                )
                if created:
                    created_count += 1

        pending_notifications = BorrowNotification.objects.filter(
            email_sent_at__isnull=True,
            notification_type__in=['APPROVED', 'DUE_TODAY', 'OVERDUE'],
        ).select_related('user', 'borrow_request', 'borrow_request__equipment')

        sent_count = 0
        failures = []
        missing_email_count = 0
        for notification in pending_notifications:
            if not notification.user.email:
                missing_email_count += 1
                continue
            try:
                if send_borrow_notification_email(notification):
                    sent_count += 1
            except (OSError, SMTPException) as error:
                failures.append(f'Notification #{notification.pk}: {error}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {created_count} due/overdue notifications; sent {sent_count} email(s).'
            )
        )
        if missing_email_count:
            self.stderr.write(
                self.style.WARNING(
                    f'{missing_email_count} notification(s) could not be emailed because the account has no email address.'
                )
            )
        if failures:
            for failure in failures:
                self.stderr.write(self.style.ERROR(failure))
            raise CommandError(
                f'{len(failures)} notification email(s) failed. They remain pending and will be retried.'
            )
