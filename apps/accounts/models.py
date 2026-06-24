from django.contrib.auth.models import AbstractUser
from django.db import models


class District(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tuman nomi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tuman"
        verbose_name_plural = "Tumanlar"
        ordering = ['name']

    def __str__(self):
        return self.name


class Organization(models.Model):
    name = models.CharField(max_length=300, verbose_name="MFY/Tashkilot nomi")
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='organizations', verbose_name="Tuman")
    address = models.CharField(max_length=500, blank=True, verbose_name="Manzil")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "MFY / Tashkilot"
        verbose_name_plural = "MFYlar / Tashkilotlar"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.district})"


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin (Nazoratchi)'),
        ('rahbar', 'Rahbar (Ijrochi)'),
        ('yetakchi', 'Yetakchi (Verifier)'),
        ('user', 'Oddiy foydalanuvchi'),
    ]

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name="Telegram ID")
    telegram_username = models.CharField(max_length=100, blank=True, verbose_name="Telegram username")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', verbose_name="Rol")
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='users', verbose_name="Tuman")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='users', verbose_name="MFY / Tashkilot")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    phone_normalized = models.CharField(max_length=20, blank=True, db_index=True,
                                        verbose_name="Telefon (raqamlar)")
    photo = models.ImageField(upload_to='users/', null=True, blank=True, verbose_name="Rasm")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def save(self, *args, **kwargs):
        # Telefonni raqamlarga keltirib indekslaymiz (qidiruv uchun)
        self.phone_normalized = ''.join(ch for ch in (self.phone or '') if ch.isdigit())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == 'super_admin' or self.is_superuser

    @property
    def is_admin(self):
        return self.role in ('super_admin', 'admin') or self.is_superuser

    @property
    def is_rahbar(self):
        return self.role == 'rahbar'

    @property
    def is_yetakchi(self):
        return self.role == 'yetakchi'

    @property
    def is_ordinary(self):
        """Oddiy foydalanuvchi — YouthGuard rollariga ega emas"""
        return self.role == 'user' and not self.is_superuser

    @staticmethod
    def normalize_phone(phone):
        """Telefonni faqat raqamlarga keltirib, oxirgi 9 raqamni qaytaradi (998901234567 -> 901234567)"""
        if not phone:
            return ''
        digits = ''.join(ch for ch in str(phone) if ch.isdigit())
        return digits[-9:] if len(digits) >= 9 else digits
