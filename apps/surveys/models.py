from django.db import models


class Survey(models.Model):
    name = models.CharField(max_length=300, verbose_name="So'rovnoma nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    is_active = models.BooleanField(default=False, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "So'rovnoma"
        verbose_name_plural = "So'rovnomalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{'✅' if self.is_active else '—'} {self.name}"

    def save(self, *args, **kwargs):
        # Agar bu so'rovnoma faol qilinayotgan bo'lsa, boshqalarini o'chiramiz
        if self.is_active:
            Survey.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def question_count(self):
        return self.questions.count()


QUESTION_TYPES = [
    ('text', 'Matn'),
    ('photo', 'Rasm'),
    ('location', 'Lokatsiya'),
    ('choice', 'Tanlov'),
    ('number', 'Raqam'),
]


class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions',
                               verbose_name="So'rovnoma")
    type = models.CharField(max_length=20, choices=QUESTION_TYPES, verbose_name="Tur")
    text = models.CharField(max_length=500, verbose_name="Savol matni")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    required = models.BooleanField(default=True, verbose_name="Majburiy")
    choices_text = models.TextField(
        blank=True,
        verbose_name="Tanlov variantlari",
        help_text="Har bir variant yangi qatorda"
    )

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.text[:60]}"

    @property
    def choices_list(self):
        if not self.choices_text:
            return []
        return [c.strip() for c in self.choices_text.splitlines() if c.strip()]
