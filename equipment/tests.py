from datetime import timedelta
from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.test import override_settings

from .models import (
    BorrowNotification, BorrowRequest, Category, CustomUser, DamageReport,
    Equipment,
)


class RegistrationTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            'username': 'new-student',
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'new.student@example.com',
            'phone': '98765 43210',
            'role': 'STUDENT',
            'department': 'Computer Science and Engineering',
            'password1': 'Violet!River82-Cloud',
            'password2': 'Violet!River82-Cloud',
        }
        data.update(overrides)
        return data

    def test_registration_page_only_offers_student_and_staff_roles(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student')
        self.assertContains(response, 'Staff')
        self.assertNotContains(response, 'Equipment Manager / Admin')
        self.assertNotContains(response, '<option value="ADMIN">')
        self.assertContains(response, '<select name="department"')
        self.assertContains(response, 'Mechanical Engineering')
        self.assertContains(response, 'Information Technology')

    def test_registration_creates_student_with_normalized_contact_details(self):
        response = self.client.post(reverse('register'), self.registration_data())

        self.assertRedirects(response, reverse('login'))
        user = CustomUser.objects.get(username='new-student')
        self.assertEqual(user.email, 'new.student@example.com')
        self.assertEqual(user.phone, '9876543210')
        self.assertEqual(user.role, 'STUDENT')

    def test_registration_rejects_admin_role_even_if_submitted_directly(self):
        response = self.client.post(
            reverse('register'),
            self.registration_data(role='ADMIN'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='new-student').exists())
        self.assertContains(response, 'Select a valid choice')

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        CustomUser.objects.create_user(
            username='existing-email',
            email='existing@example.com',
            password='Existing!Password92',
        )

        response = self.client.post(
            reverse('register'),
            self.registration_data(email='EXISTING@example.com'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this email address already exists.')
        self.assertFalse(CustomUser.objects.filter(username='new-student').exists())

    def test_registration_rejects_duplicate_mobile_after_normalizing_format(self):
        CustomUser.objects.create_user(
            username='existing-phone',
            phone='9876543210',
            password='Existing!Password92',
        )

        response = self.client.post(
            reverse('register'),
            self.registration_data(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this mobile number already exists.')
        self.assertFalse(CustomUser.objects.filter(username='new-student').exists())

    def test_registration_rejects_mobile_already_stored_with_country_code(self):
        CustomUser.objects.create_user(
            username='existing-international-phone',
            phone='919876543210',
            password='Existing!Password92',
        )

        response = self.client.post(
            reverse('register'),
            self.registration_data(phone='+91 98765 43210'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this mobile number already exists.')
        self.assertFalse(CustomUser.objects.filter(username='new-student').exists())

    def test_registration_displays_required_and_invalid_field_errors(self):
        response = self.client.post(
            reverse('register'),
            self.registration_data(email='not-an-email', phone='123'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid email address.')
        self.assertContains(response, 'Enter a valid 10-digit Indian mobile number')
        self.assertFalse(CustomUser.objects.filter(username='new-student').exists())

    def test_registration_requires_email_and_mobile_number(self):
        response = self.client.post(
            reverse('register'),
            self.registration_data(email='', phone=''),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')
        self.assertFalse(CustomUser.objects.filter(username='new-student').exists())

    def test_profile_update_rejects_duplicate_mobile_and_does_not_change_email(self):
        user = CustomUser.objects.create_user(
            username='profile-owner',
            email='owner@example.com',
            phone='9876543210',
            password='Owner!Password92',
        )
        CustomUser.objects.create_user(
            username='other-owner',
            email='other@example.com',
            phone='9123456780',
            password='Other!Password92',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('update_profile'),
            {
                'first_name': '',
                'last_name': '',
                'email': 'OTHER@example.com',
                'phone': '91234 56780',
                'department': '',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('user_home') + '#profile')
        self.assertContains(response, 'An account with this mobile number already exists.')
        user.refresh_from_db()
        self.assertEqual(user.email, 'owner@example.com')
        self.assertEqual(user.phone, '9876543210')

    def test_profile_email_is_immutable_even_if_posted_manually(self):
        user = CustomUser.objects.create_user(
            username='immutable-email',
            email='permanent@example.com',
            phone='9876543210',
            password='Owner!Password92',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('update_profile'),
            {
                'first_name': 'Updated',
                'last_name': 'Name',
                'email': 'changed@example.com',
                'phone': '9876543210',
                'department': 'Mechanical Engineering',
            },
        )

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.email, 'permanent@example.com')
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.department, 'Mechanical Engineering')

    def test_profile_accepts_formatted_indian_mobile_number_and_stores_digits(self):
        user = CustomUser.objects.create_user(
            username='formatted-phone',
            email='formatted@example.com',
            phone='9876543210',
            password='Owner!Password92',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('update_profile'),
            {
                'first_name': 'Formatted',
                'last_name': 'Phone',
                'phone': '+91 98765-43210',
                'department': 'Mechanical Engineering',
            },
        )

        self.assertRedirects(response, reverse('user_home') + '#profile')
        user.refresh_from_db()
        self.assertEqual(user.phone, '9876543210')

    def test_profile_rejects_invalid_indian_mobile_numbers_and_shows_field_error(self):
        invalid_numbers = (
            '1234567890',
            '0123456789',
            '987654321',
            '98765432101',
            '98765abc210',
        )
        for index, phone in enumerate(invalid_numbers):
            with self.subTest(phone=phone):
                existing_phone = f'98765432{index:02d}'
                user = CustomUser.objects.create_user(
                    username=f'invalid-phone-{index}',
                    email=f'invalid-{index}@example.com',
                    phone=existing_phone,
                    password='Owner!Password92',
                )
                self.client.force_login(user)
                response = self.client.post(
                    reverse('update_profile'),
                    {
                        'first_name': 'Invalid',
                        'last_name': 'Phone',
                        'phone': phone,
                        'department': 'Mechanical Engineering',
                    },
                    follow=True,
                )

                self.assertEqual(response.status_code, 200)
                expected_error = (
                    'Enter a valid 10-digit Indian mobile number, optionally prefixed with +91.'
                    if phone == '98765abc210'
                    else 'Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.'
                )
                self.assertContains(response, expected_error)
                user.refresh_from_db()
                self.assertEqual(user.phone, existing_phone)

    def test_admin_dashboard_has_no_user_role_edit_action_or_endpoint(self):
        admin = CustomUser.objects.create_superuser(
            username='dashboard-admin',
            email='dashboard-admin@example.com',
            password='Admin!Password92',
            role='ADMIN',
        )
        self.client.force_login(admin)

        response = self.client.get(reverse('admin_home'), {'tab': 'users'})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Edit Role')
        self.assertNotContains(response, 'userRoleModal')
        self.assertEqual(self.client.post('/user/role/1/').status_code, 404)

    def test_demo_seed_endpoint_is_not_exposed(self):
        self.assertEqual(self.client.get('/seed-data/').status_code, 404)


class BorrowingAndDamageReportTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='student',
            password='test-password',
            role='STUDENT',
        )
        self.other_user = CustomUser.objects.create_user(
            username='other-student',
            password='test-password',
            role='STUDENT',
        )
        self.category = Category.objects.create(name='Test category')
        self.equipment = Equipment.objects.create(
            name='Test equipment',
            code='TEST-001',
            category=self.category,
        )
        self.borrow_request = BorrowRequest.objects.create(
            user=self.user,
            equipment=self.equipment,
            start_date=timezone.localdate(),
            expected_return_date=timezone.localdate(),
            purpose='Testing',
            status='ISSUED',
            issued_at=timezone.now(),
        )
        self.client.force_login(self.user)

    def test_user_can_report_equipment_from_their_issued_request(self):
        response = self.client.post(
            reverse('report_damage'),
            {
                'borrow_request_id': self.borrow_request.id,
                'description': 'The power cable is damaged.',
            },
        )

        self.assertEqual(response.status_code, 302)
        report = DamageReport.objects.get()
        self.assertEqual(report.borrow_request, self.borrow_request)
        self.assertEqual(report.equipment, self.equipment)
        self.assertEqual(report.reported_by, self.user)

    def test_user_cannot_report_another_users_borrow_request(self):
        other_request = BorrowRequest.objects.create(
            user=self.other_user,
            equipment=self.equipment,
            start_date=timezone.localdate(),
            expected_return_date=timezone.localdate(),
            purpose='Other user testing',
            status='ISSUED',
            issued_at=timezone.now(),
        )

        response = self.client.post(
            reverse('report_damage'),
            {
                'borrow_request_id': other_request.id,
                'description': 'Unauthorized report.',
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(DamageReport.objects.exists())

    def test_user_cannot_report_equipment_not_yet_issued_to_them(self):
        not_yet_issued = BorrowRequest.objects.create(
            user=self.user,
            equipment=self.equipment,
            start_date=timezone.localdate(),
            expected_return_date=timezone.localdate(),
            purpose='Not issued yet',
            status='PENDING',
        )

        response = self.client.post(
            reverse('report_damage'),
            {
                'borrow_request_id': not_yet_issued.id,
                'description': 'Report before issue.',
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(DamageReport.objects.exists())

    def test_overdue_issued_request_is_marked_when_dashboard_loads(self):
        self.borrow_request.expected_return_date = timezone.localdate() - timedelta(days=1)
        self.borrow_request.save(update_fields=['expected_return_date'])

        response = self.client.get(reverse('user_home'))

        self.assertEqual(response.status_code, 200)
        self.borrow_request.refresh_from_db()
        self.assertEqual(self.borrow_request.status, 'OVERDUE')


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class BorrowNotificationTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            username='notification-admin',
            email='admin-notifications@example.com',
            password='Admin!Password92',
            role='ADMIN',
        )
        self.category = Category.objects.create(name='Notification equipment')
        self.equipment = Equipment.objects.create(
            name='Presentation Projector',
            code='NOTIFY-001',
            category=self.category,
        )
        self.today = timezone.localdate()

    def create_borrow_request(self, username, role, expected_return_date, status='ISSUED'):
        user = CustomUser.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='Borrower!Password92',
            role=role,
        )
        borrow_request = BorrowRequest.objects.create(
            user=user,
            equipment=self.equipment,
            quantity=1,
            start_date=self.today - timedelta(days=1),
            expected_return_date=expected_return_date,
            purpose='Project presentation',
            status=status,
            issued_at=timezone.now(),
        )
        return user, borrow_request

    def test_approval_emails_borrower_and_creates_dashboard_notification(self):
        borrower, borrow_request = self.create_borrow_request(
            'approval-borrower',
            'STUDENT',
            self.today + timedelta(days=3),
            status='PENDING',
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('approve_request', args=[borrow_request.pk]),
            {'remarks': 'Approved for class use.'},
        )

        self.assertRedirects(response, reverse('admin_home'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [borrower.email])
        self.assertIn('approved', mail.outbox[0].subject.lower())
        notification = BorrowNotification.objects.get(borrow_request=borrow_request)
        self.assertEqual(notification.notification_type, 'APPROVED')
        self.assertIsNotNone(notification.email_sent_at)

    def test_daily_command_notifies_student_and_staff_due_today_and_overdue_once(self):
        student, due_today = self.create_borrow_request(
            'due-student',
            'STUDENT',
            self.today,
        )
        staff, overdue = self.create_borrow_request(
            'overdue-staff',
            'STAFF',
            self.today - timedelta(days=1),
        )

        call_command('send_borrow_reminders', stdout=StringIO(), stderr=StringIO())
        call_command('send_borrow_reminders', stdout=StringIO(), stderr=StringIO())

        self.assertEqual(due_today.status, 'ISSUED')
        overdue.refresh_from_db()
        self.assertEqual(overdue.status, 'OVERDUE')
        self.assertEqual(
            BorrowNotification.objects.filter(
                borrow_request=due_today,
                notification_type='DUE_TODAY',
            ).count(),
            1,
        )
        self.assertEqual(
            BorrowNotification.objects.filter(
                borrow_request=overdue,
                notification_type='OVERDUE',
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual({message.to[0] for message in mail.outbox}, {student.email, staff.email})

    def test_borrower_dashboard_displays_due_date_notification(self):
        borrower, borrow_request = self.create_borrow_request(
            'dashboard-borrower',
            'STAFF',
            self.today,
        )
        BorrowNotification.objects.create(
            user=borrower,
            borrow_request=borrow_request,
            notification_type='DUE_TODAY',
            title='Equipment return due today',
            message='Please return the projector today.',
        )
        self.client.force_login(borrower)

        dashboard = reverse('staff_home') if borrower.role == 'STAFF' else reverse('user_home')
        response = self.client.get(dashboard)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Notifications')
        self.assertContains(response, 'Please return the projector today.')
