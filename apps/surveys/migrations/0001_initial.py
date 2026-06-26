from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, verbose_name="So'rovnoma nomi")),
                ('description', models.TextField(blank=True, verbose_name='Tavsif')),
                ('is_active', models.BooleanField(default=False, verbose_name='Faol')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': "So'rovnoma",
                'verbose_name_plural': "So'rovnomalar",
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(
                    choices=[('text', 'Matn'), ('photo', 'Rasm'), ('location', 'Lokatsiya'),
                             ('choice', 'Tanlov'), ('number', 'Raqam')],
                    max_length=20, verbose_name='Tur'
                )),
                ('text', models.CharField(max_length=500, verbose_name='Savol matni')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Tartib')),
                ('required', models.BooleanField(default=True, verbose_name='Majburiy')),
                ('choices_text', models.TextField(
                    blank=True,
                    help_text='Har bir variant yangi qatorda',
                    verbose_name='Tanlov variantlari'
                )),
                ('survey', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='questions',
                    to='surveys.survey',
                    verbose_name="So'rovnoma"
                )),
            ],
            options={
                'verbose_name': 'Savol',
                'verbose_name_plural': 'Savollar',
                'ordering': ['order'],
            },
        ),
    ]
