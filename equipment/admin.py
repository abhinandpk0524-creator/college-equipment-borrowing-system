from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Category, Equipment, BorrowRequest, DamageReport


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone', 'department', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('phone', 'role', 'department')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Info', {'fields': ('phone', 'role', 'department')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_class', 'created_at')
    search_fields = ('name',)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'total_quantity', 'available_quantity', 'condition', 'location')
    list_filter = ('category', 'condition')
    search_fields = ('name', 'code', 'location')


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'equipment', 'quantity', 'start_date', 'expected_return_date', 'status', 'created_at')
    list_filter = ('status', 'start_date', 'expected_return_date')
    search_fields = ('user__username', 'equipment__name', 'purpose')


@admin.register(DamageReport)
class DamageReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipment', 'reported_by', 'status', 'reported_at')
    list_filter = ('status',)
    search_fields = ('equipment__name', 'description')