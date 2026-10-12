from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import BorrowNotification


def notification_content(borrow_request, notification_type):
    equipment_name = borrow_request.equipment.name
    due_date = borrow_request.expected_return_date.strftime('%B %d, %Y')

    if notification_type == 'APPROVED':
        return (
            'Equipment request approved',
            f'Your request for {equipment_name} (quantity: {borrow_request.quantity}) '
            f'has been approved. Expected return date: {due_date}.',
        )
    if notification_type == 'DUE_TODAY':
        return (
            'Equipment return due today',
            f'{equipment_name} (quantity: {borrow_request.quantity}) is due to be '
            f'returned today, {due_date}. Please return it to the equipment office.',
        )
    if notification_type == 'OVERDUE':
        return (
            'Equipment return is overdue',
            f'{equipment_name} (quantity: {borrow_request.quantity}) was due on '
            f'{due_date} and has not been recorded as returned. Please contact the '
            'equipment office and return it as soon as possible.',
        )
    raise ValueError(f'Unsupported borrow notification type: {notification_type}')


def create_borrow_notification(borrow_request, notification_type):
    title, message = notification_content(borrow_request, notification_type)
    notification, created = BorrowNotification.objects.get_or_create(
        borrow_request=borrow_request,
        notification_type=notification_type,
        defaults={
            'user': borrow_request.user,
            'title': title,
            'message': message,
        },
    )
    return notification, created


def send_borrow_notification_email(notification):
    recipient_email = notification.user.email
    if not recipient_email:
        return False

    sent_count = send_mail(
        subject=notification.title,
        message=notification.message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=False,
    )
    if sent_count != 1:
        raise SMTPException(
            f'Email backend did not confirm delivery for notification #{notification.pk}.'
        )

    notification.email_sent_at = timezone.now()
    notification.save(update_fields=['email_sent_at'])
    return True
