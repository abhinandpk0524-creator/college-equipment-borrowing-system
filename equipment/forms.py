import re

# pyrefly: ignore [missing-import]
from django import forms
# pyrefly: ignore [missing-import]
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, Category, Equipment, BorrowRequest, DamageReport


def normalize_phone_number(phone):
    return re.sub(r'[^0-9]', '', phone)


def validate_indian_mobile_number(phone):
    phone = phone.strip()
    if not re.fullmatch(r'(?:\+?91[\s().-]*)?[0-9][0-9\s().-]*', phone):
        raise ValidationError(
            'Enter a valid 10-digit Indian mobile number, optionally prefixed with +91.'
        )

    digits = normalize_phone_number(phone)
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]

    if len(digits) != 10 or digits[0] not in '6789':
        raise ValidationError(
            'Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.'
        )
    return digits


def mobile_number_variants(phone):
    return [phone, '91' + phone, '0' + phone]


DEPARTMENT_CHOICES = (
    ('Computer Science and Engineering', 'Computer Science and Engineering'),
    ('Information Technology', 'Information Technology'),
    ('Electronics and Communication Engineering', 'Electronics and Communication Engineering'),
    ('Electrical and Electronics Engineering', 'Electrical and Electronics Engineering'),
    ('Mechanical Engineering', 'Mechanical Engineering'),
    ('Civil Engineering', 'Civil Engineering'),
    ('Artificial Intelligence and Data Science', 'Artificial Intelligence and Data Science'),
    ('Applied Sciences', 'Applied Sciences'),
    ('Administration / IT & Infrastructure', 'Administration / IT & Infrastructure'),
    ('Library', 'Library'),
    ('Other', 'Other'),
)


class RegisterForm(UserCreationForm):
    """Public registration form for student and staff accounts."""

    role = forms.ChoiceField(
        choices=(
            ('STUDENT', 'Student'),
            ('STAFF', 'Staff'),
        ),
        initial='STUDENT',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'})
    )
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10-digit Indian mobile number',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        })
    )
    department = forms.ChoiceField(
        choices=(('', 'Select a department or branch'),) + DEPARTMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label or name.capitalize()})

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def clean_phone(self):
        normalized_phone = validate_indian_mobile_number(self.cleaned_data['phone'])
        if CustomUser.objects.filter(phone__in=mobile_number_variants(normalized_phone)).exists():
            raise ValidationError('An account with this mobile number already exists.')
        return normalized_phone

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
            'department',
        ]



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon_class']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Category Description'}),
            'icon_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Icon name e.g. bi-laptop, bi-camera-video'}),
        }


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            'name', 'code', 'category', 'description',
            'location', 'total_quantity', 'available_quantity',
            'condition', 'image_url'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Equipment Name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code e.g. EQ-PRJ-01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Equipment specifications & details'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Storage Location e.g. Lab 201'}),
            'total_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'available_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'image_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Image URL or Icon Class'}),
        }


class BorrowRequestForm(forms.ModelForm):
    class Meta:
        model = BorrowRequest
        fields = ['equipment', 'quantity', 'start_date', 'expected_return_date', 'purpose']
        widgets = {
            'equipment': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Explain intended usage/event/course details'}),
        }


class ReturnEquipmentForm(forms.Form):
    return_condition = forms.ChoiceField(
        choices=Equipment.CONDITION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on condition upon return'})
    )


class DamageReportForm(forms.ModelForm):
    class Meta:
        model = DamageReport
        fields = ['equipment', 'description']
        widgets = {
            'equipment': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe issue or damage details...'}),
        }


class UserProfileForm(forms.ModelForm):
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10-digit Indian mobile number',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        })
    )
    department = forms.ChoiceField(
        choices=(('', 'Select a department or branch'),) + DEPARTMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_department = self.instance.department
        known_values = {value for value, _ in DEPARTMENT_CHOICES}
        legacy_values = {
            'Engineering': 'Engineering',
            'Computer Science & Engineering': 'Computer Science & Engineering',
            'Electronics Department': 'Electronics Department',
            'IT & Infrastructure': 'IT & Infrastructure',
        }
        if current_department and current_department not in known_values:
            label = legacy_values.get(current_department, current_department)
            self.fields['department'].choices += ((current_department, label),)

    def clean_phone(self):
        normalized_phone = validate_indian_mobile_number(self.cleaned_data['phone'])
        if CustomUser.objects.filter(
            phone__in=mobile_number_variants(normalized_phone)
        ).exclude(pk=self.instance.pk).exists():
            raise ValidationError('An account with this mobile number already exists.')
        return normalized_phone

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'department']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
