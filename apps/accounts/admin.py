from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, District, Organization


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'address', 'created_at']
    list_filter = ['district']
    search_fields = ['name', 'district__name']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'role', 'telegram_id', 'district', 'organization', 'is_active']
    list_filter = ['role', 'district', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'telegram_id', 'phone']
    ordering = ['-date_joined']

    fieldsets = UserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('telegram_id', 'telegram_username', 'role', 'district', 'organization', 'phone', 'photo')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('telegram_id', 'telegram_username', 'role', 'district', 'organization', 'phone')
        }),
    )
