import uuid
from datetime import datetime, timezone

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, FileResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Meeting, Verification, ActionLog, Document, CameraSession
from .serializers import (MeetingSerializer, MeetingCreateSerializer,
                           VerificationSerializer, VerifyActionSerializer)
from .utils import generate_pdf, log_action
from apps.youth.models import Youth
from apps.accounts.models import CustomUser


def _month_start():
    from django.utils import timezone as dtz
    from datetime import datetime as dt
    now = dtz.localtime()
    return dtz.make_aware(dt(now.year, now.month, 1))


class MeetingListCreateAPI(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return MeetingCreateSerializer if self.request.method == 'POST' else MeetingSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Meeting.objects.select_related('rahbar', 'youth').all()
        if user.role == 'rahbar':
            return qs.filter(rahbar=user)
        if user.role == 'yetakchi':
            return qs.filter(youth__yetakchi=user)
        return qs

    def perform_create(self, serializer):
        meeting = serializer.save()
        log_action(self.request.user, 'Uchrashuv yaratildi', 'Meeting', meeting.id)
        self._create_verification(meeting)

    def _create_verification(self, meeting):
        yetakchi = meeting.youth.yetakchi
        if yetakchi and meeting.status == 'pending':
            Verification.objects.create(meeting=meeting, verifier=yetakchi)


class MeetingDetailAPI(generics.RetrieveUpdateAPIView):
    serializer_class = MeetingSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Meeting.objects.all()
        if user.role == 'rahbar':
            return qs.filter(rahbar=user)
        if user.role == 'yetakchi':
            return qs.filter(youth__yetakchi=user)
        return qs


@api_view(['GET'])
def pending_verifications_api(request):
    if request.user.role not in ('yetakchi', 'admin', 'super_admin'):
        return Response({'error': 'Ruxsat yo\'q'}, status=403)

    qs = Verification.objects.filter(status='pending').select_related('meeting', 'meeting__rahbar', 'meeting__youth')
    if request.user.role == 'yetakchi':
        qs = qs.filter(verifier=request.user)

    data = VerificationSerializer(qs, many=True).data
    return Response(data)


@api_view(['POST'])
def verify_meeting_api(request, pk):
    serializer = VerifyActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    try:
        verification = Verification.objects.get(meeting_id=pk, verifier=request.user, status='pending')
    except Verification.DoesNotExist:
        return Response({'error': 'Tasdiqlash topilmadi'}, status=404)

    action = serializer.validated_data['action']
    reason = serializer.validated_data.get('reason', '')

    if action == 'approve':
        verification.status = 'approved'
        verification.meeting.status = 'verified'
        verification.verified_at = datetime.now(timezone.utc)
        generate_pdf(verification.meeting)
    else:
        verification.status = 'rejected'
        verification.rejection_reason = reason
        verification.meeting.status = 'rejected'

    verification.meeting.save()
    verification.save()
    log_action(request.user, f'Uchrashuv {action}', 'Verification', verification.id)
    return Response({'success': True, 'status': action})


@api_view(['POST'])
def impossible_meeting_api(request, pk):
    try:
        meeting = Meeting.objects.get(pk=pk, rahbar=request.user)
    except Meeting.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)

    reason = request.data.get('reason', '')
    meeting.status = 'impossible'
    meeting.impossible_reason = reason
    meeting.save()

    v, _ = Verification.objects.get_or_create(meeting=meeting, defaults={'verifier': meeting.youth.yetakchi})
    v.admin_status = 'pending'
    v.save()

    log_action(request.user, 'Uchrashuv imkonsiz', 'Meeting', meeting.id)
    return Response({'success': True})


@api_view(['POST'])
def admin_force_approve_api(request, pk):
    if not request.user.is_admin:
        return Response({'error': 'Ruxsat yo\'q'}, status=403)
    try:
        verification = Verification.objects.get(meeting_id=pk)
    except Verification.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)

    verification.admin_status = 'approved'
    verification.admin_notes = request.data.get('notes', '')
    verification.meeting.status = 'force_approved'
    verification.meeting.save()
    verification.save()
    generate_pdf(verification.meeting)
    log_action(request.user, 'Force approve', 'Meeting', pk)
    return Response({'success': True})


# ==================== BOT/WEB STATISTIKA API ====================

@api_view(['GET'])
def bot_my_youth(request):
    """Yetakchi/rahbarning yoshlari + har biriga uchrashuv statistikasi."""
    from django.utils import timezone as dtz
    user = request.user
    youths = Youth.objects.filter(is_active=True).select_related('organization')
    if user.role == 'yetakchi':
        youths = youths.filter(yetakchi=user)
    elif user.role == 'rahbar':
        youths = youths.filter(rahbar=user)

    ms = _month_start()
    now = dtz.now()
    result = []
    for y in youths:
        meetings = y.meetings.all()
        last = meetings.order_by('-date').first()
        result.append({
            'id': y.id,
            'full_name': y.full_name,
            'total_meetings': meetings.count(),
            'this_month': meetings.filter(date__gte=ms).count(),
            'last_date': last.date.strftime('%d.%m.%Y') if last else None,
            'days_ago': (now - last.date).days if last else None,
        })
    return Response(result)


@api_view(['GET'])
def bot_youth_detail(request, pk):
    """Bitta yoshning uchrashuvlar tarixi (rol bo'yicha ruxsat)."""
    from django.utils import timezone as dtz
    user = request.user
    y = get_object_or_404(Youth, pk=pk)
    if user.role == 'yetakchi' and y.yetakchi_id != user.id:
        return Response({'error': "Ruxsat yo'q"}, status=403)
    if user.role == 'rahbar' and y.rahbar_id != user.id:
        return Response({'error': "Ruxsat yo'q"}, status=403)

    ms = _month_start()
    now = dtz.now()
    meetings = y.meetings.order_by('-date')
    return Response({
        'id': y.id,
        'full_name': y.full_name,
        'age': y.age,
        'category': y.get_category_display(),
        'organization': y.organization.name if y.organization else None,
        'total_meetings': meetings.count(),
        'this_month': meetings.filter(date__gte=ms).count(),
        'meetings': [{
            'id': m.id,
            'date': m.date.strftime('%d.%m.%Y %H:%M'),
            'status': m.get_status_display(),
            'days_ago': (now - m.date).days,
        } for m in meetings[:20]],
    })


@api_view(['GET'])
def bot_my_yetakchilar(request):
    """Rahbarning yetakchilari + ularning natijalari (super_admin -> hammasi)."""
    user = request.user
    youths = Youth.objects.filter(is_active=True)
    if user.role == 'rahbar':
        youths = youths.filter(rahbar=user)
    elif user.role == 'yetakchi':
        youths = youths.filter(yetakchi=user)

    yetakchi_ids = list(youths.exclude(yetakchi=None).values_list('yetakchi', flat=True).distinct())
    ms = _month_start()
    result = []
    for yt in CustomUser.objects.filter(id__in=yetakchi_ids):
        yt_youths = youths.filter(yetakchi=yt)
        meetings = Meeting.objects.filter(youth__in=yt_youths)
        result.append({
            'id': yt.id,
            'name': yt.get_full_name() or yt.username,
            'phone': yt.phone,
            'youth_count': yt_youths.count(),
            'total_meetings': meetings.count(),
            'this_month': meetings.filter(date__gte=ms).count(),
        })
    return Response(result)


@api_view(['GET'])
def bot_my_stats(request):
    """Umumiy statistika (rol bo'yicha)."""
    user = request.user
    youths = Youth.objects.filter(is_active=True)
    meetings = Meeting.objects.all()
    if user.role == 'yetakchi':
        youths = youths.filter(yetakchi=user)
        meetings = meetings.filter(youth__yetakchi=user)
    elif user.role == 'rahbar':
        youths = youths.filter(rahbar=user)
        meetings = meetings.filter(youth__rahbar=user)

    ms = _month_start()
    verified_q = ['verified', 'force_approved']
    return Response({
        'youth_count': youths.count(),
        'total_meetings': meetings.count(),
        'this_month': meetings.filter(date__gte=ms).count(),
        'verified': meetings.filter(status__in=verified_q).count(),
        'pending': meetings.filter(status='pending').count(),
    })


@login_required
def meetings_list(request):
    from apps.accounts.models import Organization
    user = request.user
    qs = Meeting.objects.select_related('rahbar', 'rahbar__organization', 'youth', 'youth__organization').all()
    if user.role == 'rahbar':
        qs = qs.filter(rahbar=user)
    elif user.role == 'yetakchi':
        qs = qs.filter(youth__yetakchi=user)

    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    org_filter = request.GET.get('org', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if date_from:
        try:
            qs = qs.filter(date__date__gte=date_from)
        except Exception:
            pass
    if date_to:
        try:
            qs = qs.filter(date__date__lte=date_to)
        except Exception:
            pass
    if org_filter:
        qs = qs.filter(rahbar__organization_id=org_filter)

    orgs = Organization.objects.all() if user.is_admin else Organization.objects.none()

    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'meetings/list.html', {
        'page': page,
        'status_filter': status_filter,
        'status_choices': Meeting.STATUS_CHOICES,
        'date_from': date_from,
        'date_to': date_to,
        'org_filter': org_filter,
        'orgs': orgs,
    })


@login_required
def meeting_detail(request, pk):
    import json as _j
    meeting = get_object_or_404(Meeting, pk=pk)
    notes_raw = meeting.notes or ''
    if '[ANSWERS_JSON]' in notes_raw:
        parts = notes_raw.split('[ANSWERS_JSON]')
        clean_notes = parts[0].strip()
        try:
            detail_answers = _j.loads(parts[1].strip())
        except Exception:
            detail_answers = []
    else:
        clean_notes = notes_raw.strip()
        detail_answers = []
    return render(request, 'meetings/detail.html', {
        'meeting': meeting,
        'clean_notes': clean_notes,
        'detail_answers': detail_answers,
    })


@login_required
def meetings_stats(request):
    """Oylik statistika — kim necha marta uchrashgan."""
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import datetime

    # Oy tanlash (?month=YYYY-MM), aks holda joriy oy
    month_param = request.GET.get('month', '')
    now = timezone.localtime()
    try:
        year, mon = map(int, month_param.split('-'))
        sel_year, sel_month = year, mon
    except (ValueError, AttributeError):
        sel_year, sel_month = now.year, now.month

    month_start = timezone.make_aware(datetime(sel_year, sel_month, 1))
    if sel_month == 12:
        month_end = timezone.make_aware(datetime(sel_year + 1, 1, 1))
    else:
        month_end = timezone.make_aware(datetime(sel_year, sel_month + 1, 1))

    base = Meeting.objects.filter(date__gte=month_start, date__lt=month_end)
    if request.user.role == 'rahbar':
        base = base.filter(rahbar=request.user)
    elif request.user.role == 'yetakchi':
        base = base.filter(youth__yetakchi=request.user)

    verified_q = Q(status__in=['verified', 'force_approved'])

    # Rahbar bo'yicha
    rahbar_stats = list(base.values(
        'rahbar__id', 'rahbar__first_name', 'rahbar__last_name', 'rahbar__username',
        'rahbar__organization__name',
    ).annotate(
        total=Count('id'),
        verified=Count('id', filter=verified_q),
        pending=Count('id', filter=Q(status='pending')),
        rejected=Count('id', filter=Q(status='rejected')),
    ).order_by('-total'))

    # Yosh bo'yicha (eng ko'p uchrashilgan yoshlar)
    youth_stats = list(base.values(
        'youth__id', 'youth__full_name',
    ).annotate(total=Count('id')).order_by('-total')[:10])

    totals = {
        'total': base.count(),
        'verified': base.filter(verified_q).count(),
        'pending': base.filter(status='pending').count(),
        'rejected': base.filter(status='rejected').count(),
        'rahbarlar': len(rahbar_stats),
    }

    # Oxirgi 6 oy ro'yxati (selector uchun)
    months = []
    y, mo = now.year, now.month
    uz_months = ['', 'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun',
                 'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr']
    for _ in range(6):
        months.append({'value': f"{y}-{mo:02d}", 'label': f"{uz_months[mo]} {y}",
                       'active': (y == sel_year and mo == sel_month)})
        mo -= 1
        if mo == 0:
            mo = 12
            y -= 1

    return render(request, 'meetings/stats.html', {
        'rahbar_stats': rahbar_stats,
        'youth_stats': youth_stats,
        'totals': totals,
        'months': months,
        'sel_label': f"{uz_months[sel_month]} {sel_year}",
    })


@login_required
def verifications_list(request):
    user = request.user
    qs = Verification.objects.select_related('meeting', 'meeting__youth', 'meeting__rahbar', 'verifier').all()
    if user.role == 'yetakchi':
        qs = qs.filter(verifier=user)

    status_filter = request.GET.get('status', 'pending')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'meetings/verifications.html', {
        'page': page,
        'status_filter': status_filter,
    })


@login_required
def action_logs(request):
    if not request.user.is_admin:
        return HttpResponse("Ruxsat yo'q", status=403)
    qs = ActionLog.objects.select_related('user').all()
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'meetings/logs.html', {'page': page})


@login_required
def download_pdf(request, pk):
    doc = get_object_or_404(Document, meeting_id=pk)
    return FileResponse(doc.file.open(), as_attachment=True, filename=f"uchrashuv_{pk}.pdf")


@login_required
def meeting_result_view(request, pk):
    """Uchrashuv natijasi — so'rovnoma javoblari + Word yuklab olish."""
    import json
    meeting = get_object_or_404(Meeting, pk=pk)

    if request.user.role == 'rahbar' and meeting.rahbar_id != request.user.id:
        return HttpResponse("Ruxsat yo'q", status=403)

    answers = []
    notes_text = meeting.notes or ''
    if '[ANSWERS_JSON]' in notes_text:
        parts = notes_text.split('[ANSWERS_JSON]')
        try:
            answers = json.loads(parts[1].strip())
        except Exception:
            answers = []
        notes_text = parts[0].strip()

    return render(request, 'meetings/meeting_result.html', {
        'meeting': meeting,
        'answers': answers,
        'notes_text': notes_text,
    })


@login_required
def download_word_doc(request, pk):
    """Word hujjat yuklab olish."""
    import json
    from .utils import generate_word_doc
    meeting = get_object_or_404(Meeting, pk=pk)

    if request.user.role == 'rahbar' and meeting.rahbar_id != request.user.id:
        return HttpResponse("Ruxsat yo'q", status=403)

    answers = []
    if '[ANSWERS_JSON]' in (meeting.notes or ''):
        try:
            answers = json.loads(meeting.notes.split('[ANSWERS_JSON]')[1].strip())
        except Exception:
            pass

    word_bytes = generate_word_doc(meeting, answers)
    resp = HttpResponse(
        word_bytes,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    safe_name = f"uchrashuv_{meeting.id}_{meeting.youth.full_name[:20].replace(' ', '_')}.docx"
    resp['Content-Disposition'] = f'attachment; filename="{safe_name}"'
    return resp


# ─────────────── KAMERA ───────────────

def camera_page(request, session_id):
    session = get_object_or_404(CameraSession, session_id=session_id)
    return render(request, 'camera/camera.html', {'session': session})


from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
import base64, json as _json

@csrf_exempt
def camera_upload(request, session_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    session = get_object_or_404(CameraSession, session_id=session_id)

    data = _json.loads(request.body)
    photos = data.get('photos', [])

    if len(photos) >= 1 and photos[0]:
        img_data = photos[0].split(',')[-1]
        session.photo1.save(f'cam_{session_id}_1.jpg', ContentFile(base64.b64decode(img_data)), save=False)
    if len(photos) >= 2 and photos[1]:
        img_data = photos[1].split(',')[-1]
        session.photo2.save(f'cam_{session_id}_2.jpg', ContentFile(base64.b64decode(img_data)), save=False)

    session.is_submitted = True
    session.save()

    # Bot ga avtomatik xabar yuborish
    _notify_bot(session.telegram_id, session_id, len([p for p in photos if p]))

    return HttpResponse(_json.dumps({'ok': True}), content_type='application/json')


def _notify_bot(telegram_id, session_id, photo_count):
    import urllib.request
    from django.conf import settings as dj_settings
    token = getattr(dj_settings, 'BOT_TOKEN', '')
    if not token:
        return
    payload = _json.dumps({
        "chat_id": telegram_id,
        "text": f"✅ <b>{photo_count} ta rasm qabul qilindi!</b>\nDavom etish uchun tugmani bosing:",
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[{
                "text": "▶️ Davom etish",
                "callback_data": f"camera_done:{session_id}"
            }]]
        }
    }).encode()
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def camera_status(request, session_id):
    try:
        session = CameraSession.objects.get(session_id=session_id)
        return HttpResponse(_json.dumps({
            'is_submitted': session.is_submitted,
            'photo1': session.photo1.url if session.photo1 else None,
            'photo2': session.photo2.url if session.photo2 else None,
        }), content_type='application/json')
    except CameraSession.DoesNotExist:
        return HttpResponse(_json.dumps({'error': 'not found'}), status=404, content_type='application/json')


@api_view(['POST'])
@permission_classes([AllowAny])
def camera_create_api(request):
    telegram_id = request.data.get('telegram_id')
    if not telegram_id:
        return Response({'error': 'telegram_id kerak'}, status=400)
    sid = uuid.uuid4().hex
    CameraSession.objects.create(session_id=sid, telegram_id=int(telegram_id))
    return Response({'session_id': sid})
