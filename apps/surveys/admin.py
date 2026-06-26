from django.contrib import admin
from .models import Survey, Question


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('order', 'type', 'text', 'required', 'choices_text')


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'question_count', 'created_at')
    list_filter = ('is_active',)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('survey', 'order', 'type', 'text', 'required')
    list_filter = ('survey', 'type')
