from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Survey, Question, QUESTION_TYPES


@login_required
def survey_list(request):
    if not request.user.is_admin:
        return HttpResponse("Ruxsat yo'q", status=403)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            Survey.objects.create(name=name, description=description)
        return redirect('/sorovnoma/')

    surveys = Survey.objects.prefetch_related('questions').all()
    return render(request, 'surveys/list.html', {
        'surveys': surveys,
        'question_types': QUESTION_TYPES,
    })


@login_required
def survey_detail(request, pk):
    if not request.user.is_admin:
        return HttpResponse("Ruxsat yo'q", status=403)

    survey = get_object_or_404(Survey, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_question':
            q_type = request.POST.get('type', 'text')
            text = request.POST.get('text', '').strip()
            required = request.POST.get('required') == 'on'
            choices_text = request.POST.get('choices_text', '').strip()
            if text:
                last_order = survey.questions.order_by('-order').values_list('order', flat=True).first() or 0
                Question.objects.create(
                    survey=survey,
                    type=q_type,
                    text=text,
                    required=required,
                    choices_text=choices_text,
                    order=last_order + 1,
                )

        elif action == 'delete_question':
            q_id = request.POST.get('question_id')
            Question.objects.filter(pk=q_id, survey=survey).delete()

        elif action == 'move_up':
            q_id = int(request.POST.get('question_id', 0))
            q = get_object_or_404(Question, pk=q_id, survey=survey)
            prev = survey.questions.filter(order__lt=q.order).order_by('-order').first()
            if prev:
                q.order, prev.order = prev.order, q.order
                q.save(); prev.save()

        elif action == 'move_down':
            q_id = int(request.POST.get('question_id', 0))
            q = get_object_or_404(Question, pk=q_id, survey=survey)
            nxt = survey.questions.filter(order__gt=q.order).order_by('order').first()
            if nxt:
                q.order, nxt.order = nxt.order, q.order
                q.save(); nxt.save()

        elif action == 'toggle_active':
            survey.is_active = not survey.is_active
            survey.save()

        elif action == 'edit_survey':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            if name:
                survey.name = name
                survey.description = description
                survey.save()

        return redirect(f'/sorovnoma/{pk}/')

    questions = survey.questions.all()
    return render(request, 'surveys/detail.html', {
        'survey': survey,
        'questions': questions,
        'question_types': QUESTION_TYPES,
    })


@login_required
def survey_delete(request, pk):
    if not request.user.is_admin:
        return HttpResponse("Ruxsat yo'q", status=403)
    if request.method == 'POST':
        Survey.objects.filter(pk=pk).delete()
    return redirect('/sorovnoma/')


# ──── BOT API ────

@api_view(['GET'])
def api_active_survey(request):
    """Bot uchun faol so'rovnomani qaytaradi."""
    try:
        survey = Survey.objects.filter(is_active=True).prefetch_related('questions').first()
        if not survey:
            return Response({'active': False})
        return Response({
            'active': True,
            'id': survey.id,
            'name': survey.name,
            'questions': [
                {
                    'id': q.id,
                    'type': q.type,
                    'text': q.text,
                    'order': q.order,
                    'required': q.required,
                    'choices': q.choices_list,
                }
                for q in survey.questions.order_by('order')
            ]
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
