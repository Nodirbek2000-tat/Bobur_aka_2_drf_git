from django.contrib import admin
from .models import Youth


@admin.register(Youth)
class YouthAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'birth_date', 'age', 'category', 'organization', 'rahbar', 'yetakchi',
                    'total_meetings', 'is_active']
    list_filter = ['category', 'organization__district', 'organization', 'is_active']
    search_fields = ['full_name', 'address', 'phone']
    raw_id_fields = ['rahbar', 'yetakchi']
    readonly_fields = ['created_at', 'updated_at', 'age', 'total_meetings', 'approved_meetings']

    fieldsets = (
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('full_name', 'birth_date', 'age', 'address', 'phone', 'category')
        }),
        ('Bog\'liqlik', {
            'fields': ('organization', 'rahbar', 'yetakchi')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'is_active', 'total_meetings', 'approved_meetings', 'created_at', 'updated_at')
        }),
    )
