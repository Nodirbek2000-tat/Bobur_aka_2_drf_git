from django.contrib import admin
from django.utils.html import format_html
from .models import Meeting, Verification, ActionLog, Document


class VerificationInline(admin.StackedInline):
    model = Verification
    extra = 0
    readonly_fields = ['created_at', 'verified_at']


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['id', 'rahbar', 'youth', 'date', 'status_badge', 'gps_icon', 'photo_preview', 'created_at']
    list_filter = ['status', 'date', 'rahbar__district']
    search_fields = ['rahbar__username', 'rahbar__first_name', 'youth__full_name']
    readonly_fields = ['created_at', 'updated_at', 'photo_preview', 'map_link']
    inlines = [VerificationInline]
    date_hierarchy = 'date'

    def status_badge(self, obj):
        colors = {
            'pending': '#FFC107',
            'verified': '#28A745',
            'rejected': '#DC3545',
            'impossible': '#6C757D',
            'force_approved': '#17A2B8',
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:12px">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Holat'

    def gps_icon(self, obj):
        if obj.latitude and obj.longitude:
            return format_html('<span style="color:green">📍 Bor</span>')
        return format_html('<span style="color:gray">❌ Yo\'q</span>')
    gps_icon.short_description = 'GPS'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-height:80px;border-radius:4px">', obj.photo.url)
        return '—'
    photo_preview.short_description = 'Rasm'

    def map_link(self, obj):
        if obj.latitude and obj.longitude:
            url = f"https://maps.google.com/?q={obj.latitude},{obj.longitude}"
            return format_html('<a href="{}" target="_blank">🗺 Xaritada ko\'rish</a>', url)
        return '—'
    map_link.short_description = 'Xarita'


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'verifier', 'status', 'admin_status', 'verified_at', 'created_at']
    list_filter = ['status', 'admin_status']
    search_fields = ['meeting__youth__full_name', 'verifier__username']
    readonly_fields = ['created_at', 'verified_at']

    actions = ['force_approve']

    def force_approve(self, request, queryset):
        for v in queryset:
            v.admin_status = 'approved'
            v.meeting.status = 'force_approved'
            v.meeting.save()
            v.save()
        self.message_user(request, f"{queryset.count()} ta majburiy tasdiqlandi.")
    force_approve.short_description = "Majburiy tasdiqlash (Force Approve)"


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_id', 'ip_address', 'created_at']
    list_filter = ['model_name', 'created_at']
    search_fields = ['user__username', 'action']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'details', 'ip_address', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['meeting', 'qr_code', 'created_at']
    readonly_fields = ['qr_code', 'created_at']
