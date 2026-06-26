from django.db import models
from apps.accounts.models import CustomUser, Organization


class Youth(models.Model):
    CATEGORY_CHOICES = [
        ('yot_goya', "Yot g'oyalar ta'siriga tushib qolganlar"),
        ('sudlangan', "Ilgari sudlanganlar (probatsiya/profilaktika)"),
        ('mehribonlik', "Mehribonlik uyidan chiqqanlar"),
        ('probatsiya', "Probatsiya nazoratidagilar"),
        ('ijtimoiy', 'Ijtimoiy himoyaga muhtoj'),
        ('imkoniyati_cheklangan', 'Imkoniyati cheklangan'),
        ('xatarli', "Xavfli oiladan"),
        ('yetim', "Yetim yoki yolg'iz"),
        ('ishsiz', 'Ishsiz yosh'),
        ('other', 'Boshqa'),
    ]

    full_name = models.CharField(max_length=300, verbose_name="To'liq ismi")
    birth_date = models.DateField(verbose_name="Tug'ilgan sana")
    address = models.CharField(max_length=500, verbose_name="Manzil")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name="Kategoriya")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='youths', verbose_name="MFY")
    rahbar = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='assigned_youths', limit_choices_to={'role': 'rahbar'},
                                verbose_name="Mas'ul Rahbar")
    yetakchi = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='verified_youths', limit_choices_to={'role': 'yetakchi'},
                                  verbose_name="Mas'ul Yetakchi")
    notes = models.TextField(blank=True, verbose_name="Izoh")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Yosh"
        verbose_name_plural = "Yoshlar"
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.birth_date.year})"

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def total_meetings(self):
        return self.meetings.count()

    @property
    def approved_meetings(self):
        return self.meetings.filter(status__in=['verified', 'force_approved']).count()
