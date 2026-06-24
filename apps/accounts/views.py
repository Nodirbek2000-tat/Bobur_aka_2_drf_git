from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.conf import settings

from .models import CustomUser, District, Organization
from .serializers import BotAuthSerializer, UserSerializer


# ───────────── API ─────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def bot_auth(request):
    serializer = BotAuthSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    data = serializer.validated_data
    if data['secret_key'] != settings.BOT_SECRET_KEY:
        return Response({'error': "Noto'g'ri kalit"}, status=403)

    full_name = data.get('full_name', '')
    parts = full_name.strip().split(' ', 1)
    first_name = parts[0] if parts else ''
    last_name = parts[1] if len(parts) > 1 else ''

    user, created = CustomUser.objects.get_or_create(
        telegram_id=data['telegram_id'],
        defaults={
            'username': f"tg_{data['telegram_id']}",
            'first_name': first_name,
            'last_name': last_name,
            'telegram_username': data.get('username', ''),
        }
    )
    if not created:
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        user.telegram_username = data.get('username', user.telegram_username)
        user.save()

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data,
        'is_new': created,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def check_telegram(request):
    """Telegram_id bo'yicha foydalanuvchini tekshiradi (YARATMAYDI)."""
    if request.data.get('secret_key') != settings.BOT_SECRET_KEY:
        return Response({'error': "Noto'g'ri kalit"}, status=403)
    tid = request.data.get('telegram_id')
    u = CustomUser.objects.filter(telegram_id=tid).first()
    if not u:
        return Response({'exists': False})
    token, _ = Token.objects.get_or_create(user=u)
    return Response({
        'exists': True,
        'role': u.role,
        'has_phone': bool(u.phone),
        'is_ordinary': u.is_ordinary,
        'token': token.key,
        'user': UserSerializer(u).data,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def phone_lookup(request):
    """
    Bot foydalanuvchi telefon raqamini yuboradi.
    - Bazada bor bo'lsa (super_admin/admin/rahbar/yetakchi) — rolini qaytaradi va telegram_id ni bog'laydi.
    - Yo'q bo'lsa — oddiy foydalanuvchi (role='user') sifatida yaratadi.
    """
    if request.data.get('secret_key') != settings.BOT_SECRET_KEY:
        return Response({'error': "Noto'g'ri kalit"}, status=403)

    telegram_id = request.data.get('telegram_id')
    phone = request.data.get('phone', '')
    full_name = (request.data.get('full_name', '') or '').strip()
    username = request.data.get('username', '') or ''

    if not telegram_id:
        return Response({'error': 'telegram_id kerak'}, status=400)

    last9 = CustomUser.normalize_phone(phone)

    user = None
    # 1) Avval telegram_id bo'yicha (allaqachon bog'langan bo'lsa)
    user = CustomUser.objects.filter(telegram_id=telegram_id).first()
    # 2) Bo'lmasa telefon bo'yicha (admin/Excel orqali oldindan kiritilgan bo'lishi mumkin)
    if not user and last9:
        user = CustomUser.objects.filter(phone_normalized__endswith=last9).exclude(phone_normalized='').first()

    created = False
    if user:
        # Telegram ma'lumotlarini bog'lash/yangilash
        user.telegram_id = telegram_id
        if username:
            user.telegram_username = username
        if phone and not user.phone:
            user.phone = phone
        if full_name and not user.get_full_name():
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
        user.save()
    else:
        # Yangi oddiy foydalanuvchi
        parts = full_name.split(' ', 1)
        user = CustomUser.objects.create(
            username=f"tg_{telegram_id}",
            telegram_id=telegram_id,
            telegram_username=username,
            phone=phone,
            first_name=parts[0] if parts else '',
            last_name=parts[1] if len(parts) > 1 else '',
            role='user',
        )
        created = True

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'found': not created,          # bazada oldin bor edimi
        'is_new': created,
        'role': user.role,
        'is_ordinary': user.is_ordinary,
        'token': token.key,
        'user': UserSerializer(user).data,
    })


@api_view(['GET'])
def me(request):
    return Response(UserSerializer(request.user).data)


# ───────────── AUTH ─────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', '/'))
        messages.error(request, "Login yoki parol noto'g'ri")
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


def magic_login(request, token):
    """Bot bergan token orqali avtomatik web loginи"""
    from rest_framework.authtoken.models import Token as DRFToken
    try:
        drf_token = DRFToken.objects.select_related('user').get(key=token)
        user = drf_token.user
        if user.is_active:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            next_url = request.GET.get('next', '/')
            # Faqat ichki (xavfsiz) yo'llarga ruxsat
            if not next_url.startswith('/'):
                next_url = '/'
            return redirect(next_url)
    except DRFToken.DoesNotExist:
        pass
    messages.error(request, "Link yaroqsiz yoki muddati o'tgan")
    return redirect('accounts:login')


# ───────────── FOYDALANUVCHILAR ─────────────

@login_required
def users_list(request):
    if not request.user.is_admin:
        messages.error(request, "Ruxsat yo'q")
        return redirect('/')

    q = request.GET.get('q', '')
    role = request.GET.get('role', '')
    qs = CustomUser.objects.select_related('district', 'organization').order_by('role', 'first_name')

    if not request.user.is_super_admin:
        qs = qs.filter(organization=request.user.organization)

    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) |
                       Q(username__icontains=q) | Q(telegram_username__icontains=q))
    if role:
        qs = qs.filter(role=role)

    role_counts = {
        'super_admin': CustomUser.objects.filter(role='super_admin').count(),
        'admin': CustomUser.objects.filter(role='admin').count(),
        'rahbar': CustomUser.objects.filter(role='rahbar').count(),
        'yetakchi': CustomUser.objects.filter(role='yetakchi').count(),
    }
    return render(request, 'accounts/users_list.html', {
        'users': qs,
        'q': q,
        'role_filter': role,
        'role_counts': role_counts,
    })


@login_required
def user_create(request):
    if not request.user.is_admin:
        return redirect('/')

    districts = District.objects.all()
    organizations = Organization.objects.select_related('district').all()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', 'rahbar')
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        district_id = request.POST.get('district') or None
        org_id = request.POST.get('organization') or None
        telegram_id = request.POST.get('telegram_id') or None

        if not request.user.is_super_admin and role in ('super_admin', 'admin'):
            messages.error(request, "Siz faqat rahbar va yetakchi qo'sha olasiz")
            return redirect('accounts:user_create')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, f"'{username}' username allaqachon mavjud")
        elif not password or len(password) < 6:
            messages.error(request, "Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        else:
            user = CustomUser(
                username=username, first_name=first_name, last_name=last_name,
                role=role, phone=phone,
                district_id=district_id, organization_id=org_id,
            )
            if telegram_id:
                user.telegram_id = int(telegram_id)
            user.set_password(password)
            user.save()
            messages.success(request, f"{user.get_full_name() or username} muvaffaqiyatli qo'shildi!")
            return redirect('accounts:users_list')

    allowed_roles = CustomUser.ROLE_CHOICES
    if not request.user.is_super_admin:
        allowed_roles = [r for r in allowed_roles if r[0] not in ('super_admin', 'admin')]

    return render(request, 'accounts/user_form.html', {
        'title': "Yangi foydalanuvchi",
        'districts': districts,
        'organizations': organizations,
        'allowed_roles': allowed_roles,
        'edit': False,
    })


@login_required
def user_edit(request, pk):
    if not request.user.is_admin:
        return redirect('/')

    target = get_object_or_404(CustomUser, pk=pk)
    districts = District.objects.all()
    organizations = Organization.objects.select_related('district').all()

    if request.method == 'POST':
        target.first_name = request.POST.get('first_name', '').strip()
        target.last_name = request.POST.get('last_name', '').strip()
        target.phone = request.POST.get('phone', '').strip()
        target.district_id = request.POST.get('district') or None
        target.organization_id = request.POST.get('organization') or None

        new_role = request.POST.get('role', target.role)
        if request.user.is_super_admin or new_role not in ('super_admin', 'admin'):
            target.role = new_role

        new_pass = request.POST.get('password', '').strip()
        if new_pass and len(new_pass) >= 6:
            target.set_password(new_pass)

        tg = request.POST.get('telegram_id', '').strip()
        if tg:
            target.telegram_id = int(tg)

        target.save()
        messages.success(request, "O'zgarishlar saqlandi!")
        return redirect('accounts:users_list')

    allowed_roles = CustomUser.ROLE_CHOICES
    if not request.user.is_super_admin:
        allowed_roles = [r for r in allowed_roles if r[0] not in ('super_admin', 'admin')]

    return render(request, 'accounts/user_form.html', {
        'title': "Foydalanuvchini tahrirlash",
        'obj': target,
        'districts': districts,
        'organizations': organizations,
        'allowed_roles': allowed_roles,
        'edit': True,
    })


@login_required
def user_delete(request, pk):
    if not request.user.is_super_admin:
        messages.error(request, "Faqat Super Admin o'chira oladi")
        return redirect('accounts:users_list')
    target = get_object_or_404(CustomUser, pk=pk)
    if target == request.user:
        messages.error(request, "O'zingizni o'chira olmaysiz")
        return redirect('accounts:users_list')
    name = target.get_full_name() or target.username
    target.delete()
    messages.success(request, f"{name} o'chirildi")
    return redirect('accounts:users_list')


# ───────────── TUMANLAR ─────────────

@login_required
def districts_list(request):
    if not request.user.is_admin:
        return redirect('/')
    districts = District.objects.prefetch_related('organizations', 'users').all()
    return render(request, 'accounts/districts_list.html', {'districts': districts})


@login_required
def district_create(request):
    if not request.user.is_admin:
        return redirect('/')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            District.objects.create(name=name)
            messages.success(request, f"'{name}' tumani qo'shildi!")
        return redirect('accounts:districts_list')
    return redirect('accounts:districts_list')


@login_required
def district_delete(request, pk):
    if not request.user.is_super_admin:
        return redirect('accounts:districts_list')
    d = get_object_or_404(District, pk=pk)
    d.delete()
    messages.success(request, "Tuman o'chirildi")
    return redirect('accounts:districts_list')


# ───────────── MFYlar ─────────────

@login_required
def organizations_list(request):
    if not request.user.is_admin:
        return redirect('/')
    orgs = Organization.objects.select_related('district').prefetch_related('users').all()
    districts = District.objects.all()
    return render(request, 'accounts/organizations_list.html', {'orgs': orgs, 'districts': districts})


@login_required
def organization_create(request):
    if not request.user.is_admin:
        return redirect('/')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        district_id = request.POST.get('district') or None
        address = request.POST.get('address', '').strip()
        if name and district_id:
            Organization.objects.create(name=name, district_id=district_id, address=address)
            messages.success(request, f"'{name}' MFY qo'shildi!")
        else:
            messages.error(request, "Ism va tuman majburiy")
    return redirect('accounts:organizations_list')


@login_required
def organization_delete(request, pk):
    if not request.user.is_super_admin:
        return redirect('accounts:organizations_list')
    o = get_object_or_404(Organization, pk=pk)
    o.delete()
    messages.success(request, "MFY o'chirildi")
    return redirect('accounts:organizations_list')
