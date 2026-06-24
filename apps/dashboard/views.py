from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.youth.models import Youth
from apps.meetings.models import Meeting, Verification, ActionLog
from apps.accounts.models import CustomUser, District


@login_required
def home(request):
    user = request.user
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)

    if user.is_admin:
        total_youth = Youth.objects.filter(is_active=True).count()
        total_meetings = Meeting.objects.count()
        pending = Meeting.objects.filter(status='pending').count()
        verified = Meeting.objects.filter(status='verified').count()
        rejected = Meeting.objects.filter(status='rejected').count()
        impossible = Meeting.objects.filter(status='impossible').count()
        this_month = Meeting.objects.filter(created_at__gte=month_start).count()
        pending_verif = Verification.objects.filter(status='pending').count()

        # Chart data: last 7 days meetings
        days = []
        counts = []
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            cnt = Meeting.objects.filter(
                created_at__date=day.date()
            ).count()
            days.append(day.strftime('%d.%m'))
            counts.append(cnt)

        # Top rahbars
        top_rahbars = CustomUser.objects.filter(role='rahbar').annotate(
            meet_count=Count('meetings')
        ).order_by('-meet_count')[:5]

        recent_meetings = Meeting.objects.select_related('rahbar', 'youth').order_by('-created_at')[:8]
        recent_logs = ActionLog.objects.select_related('user').order_by('-created_at')[:5]

        context = {
            'total_youth': total_youth,
            'total_meetings': total_meetings,
            'pending': pending,
            'verified': verified,
            'rejected': rejected,
            'impossible': impossible,
            'this_month': this_month,
            'pending_verif': pending_verif,
            'chart_days': days,
            'chart_counts': counts,
            'top_rahbars': top_rahbars,
            'recent_meetings': recent_meetings,
            'recent_logs': recent_logs,
        }
    elif user.role == 'rahbar':
        my_meetings = Meeting.objects.filter(rahbar=user)
        context = {
            'total_youth': Youth.objects.filter(rahbar=user, is_active=True).count(),
            'total_meetings': my_meetings.count(),
            'pending': my_meetings.filter(status='pending').count(),
            'verified': my_meetings.filter(status='verified').count(),
            'rejected': my_meetings.filter(status='rejected').count(),
            'this_month': my_meetings.filter(created_at__gte=month_start).count(),
            'recent_meetings': my_meetings.select_related('youth').order_by('-created_at')[:8],
        }
    elif user.role == 'yetakchi':
        my_verif = Verification.objects.filter(verifier=user)
        context = {
            'total_youth': Youth.objects.filter(yetakchi=user, is_active=True).count(),
            'total_meetings': my_verif.count(),
            'pending': my_verif.filter(status='pending').count(),
            'verified': my_verif.filter(status='approved').count(),
            'rejected': my_verif.filter(status='rejected').count(),
            'recent_meetings': my_verif.select_related(
                'meeting', 'meeting__youth', 'meeting__rahbar'
            ).order_by('-created_at')[:8],
        }
    else:
        context = {}

    return render(request, 'dashboard/home.html', context)
