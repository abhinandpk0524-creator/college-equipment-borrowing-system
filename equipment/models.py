# pyrefly: ignore [missing-import]
from django.contrib.auth.models import AbstractUser
# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    Stores registration data for every account in the system.
    role decides whether the account is a normal user (student/staff)
    or an admin/equipment manager.
    """

    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('STAFF', 'Staff'),
        ('ADMIN', 'Admin'),
    )

    phone = models.CharField(max_length=15, blank=True, null=True, unique=True)

    email = models.EmailField(blank=True, null=True, unique=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STUDENT'
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        help_text='Department the user belongs to'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.email = (self.email or '').strip().lower() or None
        phone = ''.join(character for character in (self.phone or '') if character in '0123456789')
        self.phone = phone or None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == 'STUDENT'

    @property
    def is_staff_member(self):
        return self.role == 'STAFF'

    @property
    def is_admin_role(self):
        return self.role == 'ADMIN'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=50, default='bi-box-seam')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Equipment(models.Model):
    CONDITION_CHOICES = (
        ('GOOD', 'Good / Working'),
        ('DAMAGED', 'Damaged'),
        ('MAINTENANCE', 'Under Maintenance'),
    )

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True, help_text="e.g. EQ-PRJ-001")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='equipments')
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, default='Central Store Room')
    total_quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='GOOD')
    image_url = models.CharField(max_length=255, blank=True, help_text="Image URL or icon representation")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} [{self.code}]"

    @property
    def is_available(self):
        return self.available_quantity > 0 and self.condition == 'GOOD'


class BorrowRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ISSUED', 'Issued / On Loan'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='borrow_requests')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='borrow_requests')
    quantity = models.PositiveIntegerField(default=1)
    start_date = models.DateField()
    expected_return_date = models.DateField()
    purpose = models.TextField(help_text="Purpose of borrowing equipment")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_remarks = models.TextField(blank=True, help_text="Remarks by Admin upon approval/rejection")
    created_at = models.DateTimeField(auto_now_add=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    return_condition = models.CharField(
        max_length=20,
        choices=Equipment.CONDITION_CHOICES,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Req #{self.id} - {self.user.username} - {self.equipment.name}"

    @property
    def check_overdue(self):
        if self.status == 'ISSUED' and self.expected_return_date < timezone.now().date():
            return True
        return self.status == 'OVERDUE'


class BorrowNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('APPROVED', 'Request Approved'),
        ('DUE_TODAY', 'Return Due Today'),
        ('OVERDUE', 'Equipment Overdue'),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='borrow_notifications',
    )
    borrow_request = models.ForeignKey(
        BorrowRequest,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['borrow_request', 'notification_type'],
                name='unique_borrow_notification_per_type',
            ),
        ]

    def __str__(self):
        return f'{self.get_notification_type_display()} for request #{self.borrow_request_id}'


class DamageReport(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Reported / Open'),
        ('IN_REPAIR', 'In Repair'),
        ('RESOLVED', 'Resolved / Repaired'),
        ('REPLACED', 'Replaced / Written Off'),
    )

    borrow_request = models.ForeignKey(BorrowRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='damage_reports')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='damage_reports')
    reported_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    action_taken = models.TextField(blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"Damage Report #{self.id} for {self.equipment.name}"
