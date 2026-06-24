from django.db import models
from apps.accounts.models import CustomUser
from apps.youth.models import Youth


class Meeting(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('verified', 'Tasdiqlandi'),
        ('rejected', 'Rad etildi'),
        ('impossible', "Uchrashuv imkonsiz"),
        ('force_approved', 'Majburiy tasdiqlandi'),
    ]

    rahbar = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='meetings',
                                limit_choices_to={'role': 'rahbar'}, verbose_name="Rahbar")
    youth = models.ForeignKey(Youth, on_delete=models.CASCADE, related_name='meetings', verbose_name="Yosh")
    date = models.DateTimeField(verbose_name="Uchrashuv vaqti")
    latitude = models.FloatField(null=True, blank=True, verbose_name="Kenglik (lat)")
    longitude = models.FloatField(null=True, blank=True, verbose_name="Uzunlik (lng)")
    location_address = models.CharField(max_length=500, blank=True, verbose_name="Manzil matni")
    photo = models.ImageField(upload_to='meetings/', null=True, blank=True, verbose_name="Rasm")
    photo_taken_at = models.DateTimeField(null=True, blank=True, verbose_name="Rasm olingan vaqt")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Holat")
    notes = models.TextField(blank=True, verbose_name="Izoh")
    impossible_reason = models.TextField(blank=True, verbose_name="Imkonsizlik sababi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Uchrashuv"
        verbose_name_plural = "Uchrashuvlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rahbar} → {self.youth} ({self.date.strftime('%d.%m.%Y')})"

    @property
    def gps_valid(self):
        if not self.latitude or not self.longitude:
            return False
        if not self.youth.address:
            return True
        return True

    def get_status_color(self):
        colors = {
            'pending': 'warning',
            'verified': 'success',
            'rejected': 'danger',
            'impossible': 'secondary',
            'force_approved': 'info',
        }
        return colors.get(self.status, 'secondary')


class Verification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlandi'),
        ('rejected', 'Rad etildi'),
    ]
    ADMIN_STATUS_CHOICES = [
        ('none', 'Kerak emas'),
        ('pending', 'Admin tekshiruvi kerak'),
        ('approved', 'Admin tasdiqladi'),
        ('rejected', 'Admin rad etdi'),
    ]

    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='verification',
                                    verbose_name="Uchrashuv")
    verifier = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verifications',
                                  limit_choices_to={'role': 'yetakchi'}, verbose_name="Yetakchi")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Holat")
    rejection_reason = models.TextField(blank=True, verbose_name="Rad etish sababi")
    admin_status = models.CharField(max_length=20, choices=ADMIN_STATUS_CHOICES, default='none',
                                     verbose_name="Admin holati")
    admin_notes = models.TextField(blank=True, verbose_name="Admin izohi")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="Tasdiqlanish vaqti")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tasdiqlash"
        verbose_name_plural = "Tasdiqlashlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"Tasdiqlash: {self.meeting} ({self.get_status_display()})"


class ActionLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='action_logs',
                              verbose_name="Foydalanuvchi")
    action = models.CharField(max_length=200, verbose_name="Harakat")
    model_name = models.CharField(max_length=100, verbose_name="Model")
    object_id = models.IntegerField(null=True, blank=True, verbose_name="Ob'ekt ID")
    details = models.JSONField(default=dict, verbose_name="Tafsilotlar")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP manzil")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Harakat jurnali"
        verbose_name_plural = "Harakat jurnallari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.action} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"


class CameraSession(models.Model):
    session_id = models.CharField(max_length=64, unique=True, verbose_name="Session ID")
    telegram_id = models.BigIntegerField(verbose_name="Telegram ID")
    photo1 = models.ImageField(upload_to='camera/', null=True, blank=True, verbose_name="Rasm 1")
    photo2 = models.ImageField(upload_to='camera/', null=True, blank=True, verbose_name="Rasm 2")
    is_submitted = models.BooleanField(default=False, verbose_name="Yuborildi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kamera sessiyasi"
        verbose_name_plural = "Kamera sessiyalari"
        ordering = ['-created_at']

    def __str__(self):
        return f"Camera {self.session_id[:8]}... (tg:{self.telegram_id})"


class Document(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='document',
                                    verbose_name="Uchrashuv")
    file = models.FileField(upload_to='documents/', verbose_name="PDF fayl")
    qr_code = models.CharField(max_length=100, unique=True, verbose_name="QR kod")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Hujjat"
        verbose_name_plural = "Hujjatlar"

    def __str__(self):
        return f"Hujjat #{self.qr_code}"
