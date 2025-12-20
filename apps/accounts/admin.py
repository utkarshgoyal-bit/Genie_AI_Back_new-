from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'organization', 'is_active']
    list_filter = ['role', 'is_active', 'organization']
    search_fields = ['email', 'username']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('HR System', {'fields': ('role', 'organization', 'phone', 'is_first_login')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('HR System', {'fields': ('email', 'role', 'organization', 'phone')}),
    )