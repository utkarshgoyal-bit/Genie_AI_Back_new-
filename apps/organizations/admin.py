from django.contrib import admin
from .models import Organization, Department, Branch, Shift


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email', 'phone']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'city', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'code', 'city']


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'start_time', 'end_time', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'code']