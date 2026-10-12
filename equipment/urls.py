from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Role Dashboards
    path('user-home/', views.user_home, name='user_home'),
    path('staff-home/', views.staff_home, name='staff_home'),
    path('admin-home/', views.admin_home, name='admin_home'),

    # Borrow Request Workflows
    path('request/submit/', views.submit_borrow_request, name='submit_borrow_request'),
    path('request/cancel/<int:request_id>/', views.cancel_borrow_request, name='cancel_borrow_request'),
    path('request/approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('request/reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('request/issue/<int:request_id>/', views.issue_equipment, name='issue_equipment'),
    path('request/return/<int:request_id>/', views.return_equipment, name='return_equipment'),

    # Equipment & Category Management
    path('equipment/add/', views.add_equipment, name='add_equipment'),
    path('equipment/edit/<int:equipment_id>/', views.edit_equipment, name='edit_equipment'),
    path('equipment/delete/<int:equipment_id>/', views.delete_equipment, name='delete_equipment'),
    path('category/add/', views.add_category, name='add_category'),
    path('category/delete/<int:category_id>/', views.delete_category, name='delete_category'),

    # Damage & Maintenance Reports
    path('damage/report/', views.report_damage, name='report_damage'),
    path('damage/resolve/<int:report_id>/', views.resolve_damage, name='resolve_damage'),

    # User Profile
    path('profile/update/', views.update_profile, name='update_profile'),

]