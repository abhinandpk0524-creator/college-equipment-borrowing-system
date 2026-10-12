from smtplib import SMTPException

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    CustomUser, Category, Equipment, BorrowRequest, BorrowNotification,
    DamageReport,
)
from .forms import (
    RegisterForm, CategoryForm, EquipmentForm, BorrowRequestForm,
    ReturnEquipmentForm, DamageReportForm, UserProfileForm
)
from .notifications import create_borrow_notification, send_borrow_notification_email

User = get_user_model()


def home(request):
    """Public landing page with live system overview stats."""
    if request.user.is_authenticated:
        if request.user.role == 'ADMIN':
            return redirect('admin_home')
        elif request.user.role == 'STAFF':
            return redirect('staff_home')
        else:
            return redirect('user_home')

    total_equipment = Equipment.objects.aggregate(total=Sum('total_quantity'))['total'] or 0
    available_equipment = Equipment.objects.aggregate(total=Sum('available_quantity'))['total'] or 0
    active_loans = BorrowRequest.objects.filter(status='ISSUED').count()
    categories_count = Category.objects.count()

    context = {
        'total_equipment': total_equipment,
        'available_equipment': available_equipment,
        'active_loans': active_loans,
        'categories_count': categories_count,
    }
    return render(request, 'home.html', context)


def register(request):
    """Registers a student or staff account with validation errors shown inline."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account for {user.username} created successfully! Please login.')
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def user_login(request):
    """Authenticates user and redirects to role-specific dashboard."""
    if request.user.is_authenticated:
        if request.user.role == 'ADMIN':
            return redirect('admin_home')
        elif request.user.role == 'STAFF':
            return redirect('staff_home')
        else:
            return redirect('user_home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            if user.role == 'ADMIN':
                return redirect('admin_home')
            elif user.role == 'STAFF':
                return redirect('staff_home')
            else:
                return redirect('user_home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


# ==========================================
# 1. USER (STUDENT) VIEW PAGE
# ==========================================
@login_required
def user_home(request):
    """Complete Student View Dashboard."""
    # Handle role restriction if needed, but allow students
    if request.user.role == 'ADMIN':
        return redirect('admin_home')
    elif request.user.role == 'STAFF':
        return redirect('staff_home')

    # Search & Filter for Equipment
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    
    equipments = Equipment.objects.all()
    if query:
        equipments = equipments.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )
    if category_id:
        equipments = equipments.filter(category_id=category_id)

    categories = Category.objects.all()
    my_requests = BorrowRequest.objects.filter(user=request.user)

    # Check and update overdue status dynamically
    today = timezone.now().date()
    for req in my_requests:
        if req.status == 'ISSUED' and req.expected_return_date < today:
            req.status = 'OVERDUE'
            req.save()

    my_damage_reports = DamageReport.objects.filter(reported_by=request.user)
    reportable_borrow_requests = my_requests.filter(
        issued_at__isnull=False
    ).select_related('equipment')

    stats = {
        'total_requests': my_requests.count(),
        'pending': my_requests.filter(status='PENDING').count(),
        'approved': my_requests.filter(status='APPROVED').count(),
        'issued': my_requests.filter(status='ISSUED').count(),
        'returned': my_requests.filter(status='RETURNED').count(),
        'overdue': my_requests.filter(status='OVERDUE').count(),
    }

    profile_form = UserProfileForm(instance=request.user)
    borrow_notifications = BorrowNotification.objects.filter(
        user=request.user
    ).select_related('borrow_request')[:10]

    context = {
        'equipments': equipments,
        'categories': categories,
        'my_requests': my_requests,
        'reportable_borrow_requests': reportable_borrow_requests,
        'my_damage_reports': my_damage_reports,
        'stats': stats,
        'profile_form': profile_form,
        'borrow_notifications': borrow_notifications,
        'selected_category': category_id,
        'search_query': query,
        'today_date': today.strftime('%Y-%m-%d'),
    }
    return render(request, 'user_home.html', context)


# ==========================================
# 2. STAFF VIEW PAGE
# ==========================================
@login_required
def staff_home(request):
    """Complete Staff View Dashboard."""
    if request.user.role == 'ADMIN':
        return redirect('admin_home')
    elif request.user.role == 'STUDENT':
        return redirect('user_home')

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')

    equipments = Equipment.objects.all()
    if query:
        equipments = equipments.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query)
        )
    if category_id:
        equipments = equipments.filter(category_id=category_id)

    categories = Category.objects.all()
    staff_requests = BorrowRequest.objects.filter(user=request.user)

    today = timezone.now().date()
    for req in staff_requests:
        if req.status == 'ISSUED' and req.expected_return_date < today:
            req.status = 'OVERDUE'
            req.save()

    active_loans = staff_requests.filter(status__in=['ISSUED', 'APPROVED'])
    staff_damage_reports = DamageReport.objects.filter(reported_by=request.user)
    reportable_borrow_requests = staff_requests.filter(
        issued_at__isnull=False
    ).select_related('equipment')

    stats = {
        'total_requests': staff_requests.count(),
        'active_loans': active_loans.count(),
        'pending': staff_requests.filter(status='PENDING').count(),
        'returned': staff_requests.filter(status='RETURNED').count(),
        'overdue': staff_requests.filter(status='OVERDUE').count(),
    }

    profile_form = UserProfileForm(instance=request.user)
    borrow_notifications = BorrowNotification.objects.filter(
        user=request.user
    ).select_related('borrow_request')[:10]

    context = {
        'equipments': equipments,
        'categories': categories,
        'staff_requests': staff_requests,
        'reportable_borrow_requests': reportable_borrow_requests,
        'active_loans': active_loans,
        'staff_damage_reports': staff_damage_reports,
        'stats': stats,
        'profile_form': profile_form,
        'borrow_notifications': borrow_notifications,
        'selected_category': category_id,
        'search_query': query,
        'today_date': today.strftime('%Y-%m-%d'),
    }
    return render(request, 'staff_home.html', context)


# ==========================================
# 3. ADMIN VIEW PAGE & MODULES
# ==========================================
@login_required
def admin_home(request):
    """Complete Admin Dashboard & Management Hub."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied! Admin privileges required.')
        if request.user.role == 'STAFF':
            return redirect('staff_home')
        return redirect('user_home')

    today = timezone.now().date()
    # Update all issued requests to overdue if past expected return date
    BorrowRequest.objects.filter(status='ISSUED', expected_return_date__lt=today).update(status='OVERDUE')

    # Search & Filter
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    tab = request.GET.get('tab', 'overview')

    equipments = Equipment.objects.all().select_related('category')
    if query:
        equipments = equipments.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(location__icontains=query)
        )
    if category_id:
        equipments = equipments.filter(category_id=category_id)

    categories = Category.objects.all().annotate(item_count=Count('equipments'))
    pending_requests = BorrowRequest.objects.filter(status='PENDING').select_related('user', 'equipment')
    all_requests = BorrowRequest.objects.all().select_related('user', 'equipment')
    issued_requests = BorrowRequest.objects.filter(status='ISSUED').select_related('user', 'equipment')
    overdue_requests = BorrowRequest.objects.filter(status='OVERDUE').select_related('user', 'equipment')
    damage_reports = DamageReport.objects.all().select_related('equipment', 'reported_by', 'borrow_request')
    users_list = User.objects.all().order_by('-date_joined')

    # Aggregated Stats
    total_qty = Equipment.objects.aggregate(total=Sum('total_quantity'))['total'] or 0
    available_qty = Equipment.objects.aggregate(total=Sum('available_quantity'))['total'] or 0

    kpis = {
        'total_equipment_types': Equipment.objects.count(),
        'total_qty': total_qty,
        'available_qty': available_qty,
        'active_loans': issued_requests.count(),
        'pending_requests': pending_requests.count(),
        'overdue_count': overdue_requests.count(),
        'damaged_count': damage_reports.filter(status__in=['OPEN', 'IN_REPAIR']).count(),
        'total_users': users_list.count(),
    }

    category_form = CategoryForm()
    equipment_form = EquipmentForm()

    context = {
        'kpis': kpis,
        'equipments': equipments,
        'categories': categories,
        'pending_requests': pending_requests,
        'all_requests': all_requests,
        'issued_requests': issued_requests,
        'overdue_requests': overdue_requests,
        'damage_reports': damage_reports,
        'users_list': users_list,
        'category_form': category_form,
        'equipment_form': equipment_form,
        'active_tab': tab,
        'search_query': query,
        'selected_category': category_id,
        'today_date': today.strftime('%Y-%m-%d'),
    }
    return render(request, 'admin_home.html', context)


# ==========================================
# WORKFLOW ACTION ENDPOINTS
# ==========================================

@login_required
def submit_borrow_request(request):
    """Submits borrowing request for Student or Staff."""
    if request.method == 'POST':
        equipment_id = request.POST.get('equipment')
        quantity = int(request.POST.get('quantity', 1))
        start_date_str = request.POST.get('start_date')
        expected_return_date_str = request.POST.get('expected_return_date')
        purpose = request.POST.get('purpose', '').strip()

        equipment = get_object_or_404(Equipment, id=equipment_id)

        # Validations
        if quantity <= 0:
            messages.error(request, 'Quantity must be at least 1.')
            return redirect(request.META.get('HTTP_REFERER', 'user_home'))

        if quantity > equipment.available_quantity:
            messages.error(request, f'Requested quantity ({quantity}) exceeds available stock ({equipment.available_quantity}).')
            return redirect(request.META.get('HTTP_REFERER', 'user_home'))

        if equipment.condition != 'GOOD':
            messages.error(request, 'This equipment is currently marked as Damaged or Under Maintenance.')
            return redirect(request.META.get('HTTP_REFERER', 'user_home'))

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            expected_return_date = datetime.strptime(expected_return_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, 'Invalid date format selected.')
            return redirect(request.META.get('HTTP_REFERER', 'user_home'))

        if expected_return_date < start_date:
            messages.error(request, 'Expected return date cannot be earlier than start date.')
            return redirect(request.META.get('HTTP_REFERER', 'user_home'))

        BorrowRequest.objects.create(
            user=request.user,
            equipment=equipment,
            quantity=quantity,
            start_date=start_date,
            expected_return_date=expected_return_date,
            purpose=purpose,
            status='PENDING'
        )

        messages.success(request, f'Borrowing request for "{equipment.name}" submitted successfully! Awaiting admin approval.')

    return redirect(request.META.get('HTTP_REFERER', 'user_home'))


@login_required
def cancel_borrow_request(request, request_id):
    """Allows user to cancel their own pending request."""
    borrow_req = get_object_or_404(BorrowRequest, id=request_id)
    if borrow_req.user != request.user and request.user.role != 'ADMIN':
        messages.error(request, 'Unauthorized action.')
        return redirect(request.META.get('HTTP_REFERER', 'user_home'))

    if borrow_req.status == 'PENDING':
        borrow_req.delete()
        messages.success(request, 'Borrowing request cancelled successfully.')
    else:
        messages.error(request, 'Only pending requests can be cancelled.')

    return redirect(request.META.get('HTTP_REFERER', 'user_home'))


@login_required
def approve_request(request, request_id):
    """Admin approves a pending borrowing request."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    borrow_req = get_object_or_404(BorrowRequest, id=request_id)
    if request.method == 'POST':
        if borrow_req.status != 'PENDING':
            messages.error(request, 'Only pending requests can be approved.')
            return redirect('admin_home')

        remarks = request.POST.get('remarks', '').strip()
        equipment = borrow_req.equipment

        if borrow_req.quantity > equipment.available_quantity:
            messages.error(request, f'Cannot approve! Not enough stock available (Available: {equipment.available_quantity}).')
            return redirect('admin_home')

        borrow_req.status = 'APPROVED'
        borrow_req.admin_remarks = remarks
        borrow_req.save()

        messages.success(request, f'Request #{borrow_req.id} for {borrow_req.user.username} has been APPROVED.')
        notification, _ = create_borrow_notification(borrow_req, 'APPROVED')
        if not notification.user.email:
            messages.warning(
                request,
                f'Request approved, but no email was sent because {notification.user.username} has no email address.',
            )
        elif notification.email_sent_at is None:
            try:
                send_borrow_notification_email(notification)
            except (OSError, SMTPException) as error:
                messages.error(
                    request,
                    f'Request approved, but the email could not be sent ({error}). '
                    'It remains queued for retry by the daily reminder task.',
                )
    return redirect('admin_home')


@login_required
def reject_request(request, request_id):
    """Admin rejects a borrowing request."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    borrow_req = get_object_or_404(BorrowRequest, id=request_id)
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '').strip()
        borrow_req.status = 'REJECTED'
        borrow_req.admin_remarks = remarks
        borrow_req.save()

        messages.info(request, f'Request #{borrow_req.id} for {borrow_req.user.username} was REJECTED.')
    return redirect('admin_home')


@login_required
def issue_equipment(request, request_id):
    """Admin issues approved equipment to user."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    borrow_req = get_object_or_404(BorrowRequest, id=request_id)
    equipment = borrow_req.equipment

    if equipment.available_quantity < borrow_req.quantity:
        messages.error(request, f'Insufficient stock available to issue item! (Available: {equipment.available_quantity})')
        return redirect('admin_home')

    borrow_req.status = 'ISSUED'
    borrow_req.issued_at = timezone.now()
    borrow_req.save()

    # Deduct stock
    equipment.available_quantity -= borrow_req.quantity
    equipment.save()

    messages.success(request, f'Equipment "{equipment.name}" issued to {borrow_req.user.username}. Quantity on loan: {borrow_req.quantity}.')
    return redirect('admin_home')


@login_required
def return_equipment(request, request_id):
    """Admin records equipment return & checks item condition."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    borrow_req = get_object_or_404(BorrowRequest, id=request_id)
    if request.method == 'POST':
        condition = request.POST.get('return_condition', 'GOOD')
        remarks = request.POST.get('remarks', '').strip()

        equipment = borrow_req.equipment

        borrow_req.status = 'RETURNED'
        borrow_req.returned_at = timezone.now()
        borrow_req.return_condition = condition
        if remarks:
            borrow_req.admin_remarks = f"{borrow_req.admin_remarks}\n[Return Note]: {remarks}".strip()
        borrow_req.save()

        # Restock equipment
        equipment.available_quantity += borrow_req.quantity
        if condition in ['DAMAGED', 'MAINTENANCE']:
            equipment.condition = condition
            # Create a damage report automatically
            DamageReport.objects.create(
                borrow_request=borrow_req,
                equipment=equipment,
                reported_by=request.user,
                description=f"Returned in {condition} condition by {borrow_req.user.username}. Notes: {remarks}",
                status='OPEN'
            )
        equipment.save()

        messages.success(request, f'Equipment return recorded for Request #{borrow_req.id}. Stock updated!')
    return redirect('admin_home')


# ==========================================
# ADMIN CRUD ENDPOINTS
# ==========================================

@login_required
def add_equipment(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            eq = form.save()
            messages.success(request, f'Equipment "{eq.name}" [{eq.code}] created successfully!')
        else:
            for error in form.errors.values():
                messages.error(request, str(error))
    return redirect('admin_home')


@login_required
def edit_equipment(request, equipment_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    equipment = get_object_or_404(Equipment, id=equipment_id)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Equipment "{equipment.name}" updated successfully!')
        else:
            messages.error(request, 'Failed to update equipment details.')
    return redirect('admin_home')


@login_required
def delete_equipment(request, equipment_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    equipment = get_object_or_404(Equipment, id=equipment_id)
    eq_name = equipment.name
    equipment.delete()
    messages.success(request, f'Equipment "{eq_name}" deleted.')
    return redirect('admin_home')


@login_required
def add_category(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f'Category "{cat.name}" added!')
        else:
            messages.error(request, 'Category could not be added. Check name uniqueness.')
    return redirect('admin_home')


@login_required
def delete_category(request, category_id):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    cat = get_object_or_404(Category, id=category_id)
    cat_name = cat.name
    cat.delete()
    messages.success(request, f'Category "{cat_name}" deleted.')
    return redirect('admin_home')


@login_required
@require_POST
def report_damage(request):
    """Submits a damage report for equipment the user was issued."""
    borrow_req_id = request.POST.get('borrow_request_id')
    description = request.POST.get('description', '').strip()
    borrow_req = get_object_or_404(
        BorrowRequest.objects.select_related('equipment'),
        id=borrow_req_id,
        user=request.user,
        issued_at__isnull=False,
    )

    if not description:
        messages.error(request, 'Please describe the equipment issue before submitting.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    DamageReport.objects.create(
        borrow_request=borrow_req,
        equipment=borrow_req.equipment,
        reported_by=request.user,
        description=description,
        status='OPEN'
    )

    messages.success(
        request,
        f'Damage report submitted for "{borrow_req.equipment.name}". Maintenance team notified.'
    )

    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def resolve_damage(request, report_id):
    """Admin updates maintenance status for damage report."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Admin privileges required.')
        return redirect('home')

    report = get_object_or_404(DamageReport, id=report_id)
    if request.method == 'POST':
        status = request.POST.get('status', 'OPEN')
        action_taken = request.POST.get('action_taken', '').strip()

        report.status = status
        report.action_taken = action_taken
        report.save()

        # Update equipment condition if resolved
        if status == 'RESOLVED':
            report.equipment.condition = 'GOOD'
            report.equipment.save()
        elif status == 'IN_REPAIR':
            report.equipment.condition = 'MAINTENANCE'
            report.equipment.save()

        messages.success(request, f'Damage report #{report.id} updated to {status}.')

    return redirect('admin_home')


@login_required
def update_profile(request):
    """Updates user contact and department info."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
        else:
            for field, errors in form.errors.items():
                field_label = form.fields[field].label or field.replace('_', ' ').capitalize()
                for error in errors:
                    messages.error(request, f'{field_label}: {error}')

    if request.user.role == 'STAFF':
        return redirect(f"{reverse('staff_home')}#staff-profile")
    if request.user.role == 'STUDENT':
        return redirect(f"{reverse('user_home')}#profile")
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

