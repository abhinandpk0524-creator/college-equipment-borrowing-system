from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from equipment.models import Category, Equipment, BorrowRequest


class Command(BaseCommand):
    help = 'Seeds initial demo users, categories, equipment, and borrow records.'

    def handle(self, *args, **options):
        User = get_user_model()
        self.stdout.write("Seeding demo users...")

        # 1. Admin
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@college.edu',
                'first_name': 'System',
                'last_name': 'Admin',
                'role': 'ADMIN',
                'department': 'IT & Infrastructure',
                'phone': '9876543210',
            }
        )
        admin_user.set_password('admin123')
        admin_user.role = 'ADMIN'
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        # 2. Staff
        staff_user, _ = User.objects.get_or_create(
            username='staff1',
            defaults={
                'email': 'prof.john@college.edu',
                'first_name': 'John',
                'last_name': 'Smith',
                'role': 'STAFF',
                'department': 'Computer Science & Engineering',
                'phone': '9876543211',
            }
        )
        staff_user.set_password('staff123')
        staff_user.role = 'STAFF'
        staff_user.save()

        # 3. Student
        student_user, _ = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'alice.student@college.edu',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'role': 'STUDENT',
                'department': 'Electronics Department',
                'phone': '9876543212',
            }
        )
        student_user.set_password('student123')
        student_user.role = 'STUDENT'
        student_user.save()

        self.stdout.write("Seeding categories...")
        cat_av, _ = Category.objects.get_or_create(
            name='Audio Visual & Projectors',
            defaults={'description': 'Projectors, display screens, and presentation tools.', 'icon_class': 'bi-display'}
        )
        cat_computing, _ = Category.objects.get_or_create(
            name='Computers & Laptops',
            defaults={'description': 'High performance laptops, tablets, and workstations.', 'icon_class': 'bi-laptop'}
        )
        cat_lab, _ = Category.objects.get_or_create(
            name='Lab Instruments',
            defaults={'description': 'Oscilloscopes, multimeters, and electronic test rigs.', 'icon_class': 'bi-cpu'}
        )
        cat_media, _ = Category.objects.get_or_create(
            name='Cameras & Media Tech',
            defaults={'description': 'DSLR cameras, tripod stands, and microphones.', 'icon_class': 'bi-camera-video'}
        )
        cat_sports, _ = Category.objects.get_or_create(
            name='Sports & Event Gear',
            defaults={'description': 'Public address systems, podium mics, and sports equipment.', 'icon_class': 'bi-speaker'}
        )

        self.stdout.write("Seeding equipment...")
        eq1, _ = Equipment.objects.get_or_create(
            code='EQ-PRJ-4K',
            defaults={
                'name': 'Epson 4K Laser Projector',
                'category': cat_av,
                'description': '3500 Lumens HDMI/Wireless 4K classroom projector.',
                'location': 'AV Store - Room 102',
                'total_quantity': 5,
                'available_quantity': 3,
                'condition': 'GOOD',
                'image_url': 'bi-projector'
            }
        )
        eq2, _ = Equipment.objects.get_or_create(
            code='EQ-LAP-MAC',
            defaults={
                'name': 'Apple MacBook Pro 16" (M2)',
                'category': cat_computing,
                'description': 'High spec workstation laptop for media processing and lab work.',
                'location': 'CS Dept Lab - Rack 4',
                'total_quantity': 10,
                'available_quantity': 7,
                'condition': 'GOOD',
                'image_url': 'bi-laptop'
            }
        )
        eq3, _ = Equipment.objects.get_or_create(
            code='EQ-OSC-200',
            defaults={
                'name': 'Tektronix Digital Oscilloscope 200MHz',
                'category': cat_lab,
                'description': '4-channel digital storage oscilloscope for electronics lab experiments.',
                'location': 'Electronics Lab 2',
                'total_quantity': 8,
                'available_quantity': 5,
                'condition': 'GOOD',
                'image_url': 'bi-cpu'
            }
        )
        eq4, _ = Equipment.objects.get_or_create(
            code='EQ-CAM-SONY',
            defaults={
                'name': 'Sony Alpha A7 IV Cinema Camera',
                'category': cat_media,
                'description': 'Full frame 4K video recording kit with 24-70mm GM lens.',
                'location': 'Media Center - Cabinet A',
                'total_quantity': 4,
                'available_quantity': 2,
                'condition': 'GOOD',
                'image_url': 'bi-camera-reels'
            }
        )
        eq5, _ = Equipment.objects.get_or_create(
            code='EQ-PA-SYS',
            defaults={
                'name': 'Yamaha Portable PA System 500W',
                'category': cat_sports,
                'description': 'Portable sound system with dual wireless mics for auditorium events.',
                'location': 'Main Auditorium Store',
                'total_quantity': 3,
                'available_quantity': 2,
                'condition': 'GOOD',
                'image_url': 'bi-speaker'
            }
        )

        self.stdout.write("Seeding sample borrow requests...")
        today = timezone.localdate()
        BorrowRequest.objects.get_or_create(
            user=student_user,
            equipment=eq1,
            start_date=today,
            expected_return_date=today + timedelta(days=3),
            defaults={
                'quantity': 1,
                'purpose': 'Final Year Project Presentation in Seminar Hall.',
                'status': 'PENDING'
            }
        )

        BorrowRequest.objects.get_or_create(
            user=staff_user,
            equipment=eq2,
            start_date=today - timedelta(days=2),
            expected_return_date=today + timedelta(days=5),
            defaults={
                'quantity': 1,
                'purpose': 'Conducting Advanced AI & Machine Learning Workshop.',
                'status': 'ISSUED',
                'issued_at': timezone.now() - timedelta(days=2)
            }
        )

        BorrowRequest.objects.get_or_create(
            user=student_user,
            equipment=eq3,
            start_date=today - timedelta(days=10),
            expected_return_date=today - timedelta(days=2),
            defaults={
                'quantity': 1,
                'purpose': 'Circuit design experiment in Lab 2.',
                'status': 'OVERDUE',
                'issued_at': timezone.now() - timedelta(days=10)
            }
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("Credentials:"))
        self.stdout.write("  Admin:   admin / admin123")
        self.stdout.write("  Staff:   staff1 / staff123")
        self.stdout.write("  Student: student1 / student123")
