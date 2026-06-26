#!/bin/bash
# ================================================================
#  YouthGuard — To'liq tizim tekshiruvi
#  Ishlatish: bash health_check.sh
# ================================================================

C='\033[0;36m'; G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; N='\033[0m'
ok()  { echo -e "  ${G}✅  $1${N}"; }
err() { echo -e "  ${R}❌  $1${N}"; }
warn(){ echo -e "  ${Y}⚠️   $1${N}"; }
hdr() { echo -e "\n${C}━━━ $1 ━━━${N}"; }

echo -e "\n${C}╔══════════════════════════════════════════════╗"
echo -e "║   YouthGuard — To'liq Tizim Tekshiruvi      ║"
echo -e "╚══════════════════════════════════════════════╝${N}"
echo "   $(date '+%d.%m.%Y %H:%M:%S')"

# ──────────────────────────────────────────────
hdr "1. KONTEYNERLAR HOLATI"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker compose ps

# ──────────────────────────────────────────────
hdr "2. MIGRATSIYALAR TEKSHIRUVI"
MIG=$(docker compose exec -T web python manage.py migrate --check 2>&1)
if echo "$MIG" | grep -q "No migrations"; then
    ok "Barcha migratsiyalar bajarilgan"
elif echo "$MIG" | grep -q "unapplied"; then
    err "Bajarilmagan migratsiyalar bor! → 'docker compose exec web python manage.py migrate'"
    echo "$MIG" | grep "unapplied" | head -5
else
    ok "Migratsiya holati: OK"
fi

# ──────────────────────────────────────────────
hdr "3. DATABASE STATISTIKA"
docker compose exec -T web python manage.py shell << 'PYEOF'
from apps.accounts.models import CustomUser, Organization, District
from apps.youth.models import Youth
from apps.meetings.models import Meeting, Verification

# Foydalanuvchilar
print("\n  👥 FOYDALANUVCHILAR (rol bo'yicha):")
roles = [('super_admin','Super Admin'),('admin','Admin'),('rahbar','Rahbar'),('yetakchi','Yetakchi'),('user','Oddiy')]
for role, label in roles:
    total = CustomUser.objects.filter(role=role).count()
    if total == 0:
        continue
    with_tg = CustomUser.objects.filter(role=role, telegram_id__isnull=False).count()
    no_tg   = total - with_tg
    icon    = "✅" if with_tg > 0 else "⚠️ "
    print(f"    {icon} {label:12s}: {total:3d} ta  |  Bot ulangan: {with_tg}  |  Ulanmagan: {no_tg}")

# Tuman va MFYlar
print(f"\n  🗺️  TUMAN/MFY: {District.objects.count()} ta tuman, {Organization.objects.count()} ta MFY")

# Yoshlar
print("\n  👤 YOSHLAR:")
total_y   = Youth.objects.filter(is_active=True).count()
no_rahbar = Youth.objects.filter(is_active=True, rahbar__isnull=True).count()
no_yetakchi= Youth.objects.filter(is_active=True, yetakchi__isnull=True).count()
no_org    = Youth.objects.filter(is_active=True, organization__isnull=True).count()
print(f"    Jami faol: {total_y} ta")
if no_rahbar:   print(f"    ⚠️  Rahbarsiz: {no_rahbar} ta yosh")
if no_yetakchi: print(f"    ⚠️  Yetakchisiz: {no_yetakchi} ta yosh")
if no_org:      print(f"    ⚠️  MFYsiz: {no_org} ta yosh")
if not no_rahbar and not no_yetakchi and not no_org:
    print("    ✅ Barcha yoshlarga rahbar va yetakchi biriktirilgan")

# Uchrashuvlar
print("\n  🤝 UCHRASHUVLAR (status bo'yicha):")
for status, label in Meeting.STATUS_CHOICES:
    c = Meeting.objects.filter(status=status).count()
    if c > 0:
        icon = "✅" if status in ("verified","force_approved") else "⏳" if status == "pending" else "❌"
        print(f"    {icon} {label:25s}: {c} ta")
total_m   = Meeting.objects.count()
with_gps  = Meeting.objects.filter(latitude__isnull=False).count()
with_photo= Meeting.objects.exclude(photo='').exclude(photo__isnull=True).count()
no_gps    = total_m - with_gps
print(f"\n    Jami: {total_m} ta  |  GPS bor: {with_gps}  |  GPS YO'Q: {no_gps}  |  Rasm: {with_photo} ta")

# Tasdiqlashlar
print("\n  ✅ TASDIQLASHLAR (kutilayotgan):")
pending_v = Verification.objects.filter(status='pending').count()
if pending_v:
    print(f"    ⏳ Yetakchi tasdiqlashini kutayotgan: {pending_v} ta")
else:
    print("    ✅ Tasdiqlash kutayotgan yo'q")

PYEOF

# ──────────────────────────────────────────────
hdr "4. SO'ROVNOMA HOLATI"
docker compose exec -T web python manage.py shell << 'PYEOF'
try:
    from apps.surveys.models import Survey, Question
    surveys = Survey.objects.all()
    if not surveys.exists():
        print("  ❌ Hali hech qanday so'rovnoma yaratilmagan!")
        print("     → sam-auth.uz/sorovnoma/ ga kiring va yarating")
    else:
        active = surveys.filter(is_active=True).first()
        if active:
            print(f"  ✅ FAOL so'rovnoma: '{active.name}'")
            qs = active.questions.all()
            print(f"     Savollar soni: {qs.count()} ta")
            for q in qs:
                req = "majburiy" if q.required else "ixtiyoriy"
                print(f"     {q.order}. [{q.type:8s}] {q.text[:55]:55s} ({req})")
        else:
            print("  ⚠️  So'rovnoma bor, lekin HECH BIRI FAOL EMAS!")
            print("     → /sorovnoma/ ga kirib, faollashtiring")
        print(f"\n  Barcha so'rovnomalar ({surveys.count()} ta):")
        for s in surveys:
            st = "✅ FAOL" if s.is_active else "⏸  nofaol"
            print(f"    [{st}] {s.name} — {s.questions.count()} savol")
except Exception as e:
    print(f"  ❌ So'rovnomalar moduli yuklanmagan: {e}")
    print("     → 'docker compose exec web python manage.py migrate' bajaring")
PYEOF

# ──────────────────────────────────────────────
hdr "5. API ENDPOINTLAR TEKSHIRUVI"

# Token olish
TOKEN=$(docker compose exec -T web python manage.py shell -c "
from rest_framework.authtoken.models import Token
from apps.accounts.models import CustomUser
u = CustomUser.objects.filter(role='super_admin').first()
if not u:
    u = CustomUser.objects.filter(is_superuser=True).first()
if u:
    t, _ = Token.objects.get_or_create(user=u)
    print(t.key)
" 2>/dev/null | tr -d '\r\n ')

if [ -z "$TOKEN" ]; then
    warn "Super admin topilmadi — API testi o'tkazib yuborildi"
else
    echo "  🔑 Test tokeni: ${TOKEN:0:12}..."
    BASE="https://sam-auth.uz"
    declare -A ENDPOINTS=(
        ["/uchrashuvlar/api/list/"]="Uchrashuvlar ro'yxati"
        ["/uchrashuvlar/api/my-youth/"]="Bot: mening yoshlarim"
        ["/uchrashuvlar/api/my-stats/"]="Bot: statistika"
        ["/uchrashuvlar/api/pending-verifications/"]="Tasdiqlash kutayotganlar"
        ["/sorovnoma/api/active/"]="Faol so'rovnoma (bot)"
        ["/yoshlar/api/"]="Yoshlar API"
        ["/accounts/api/check-telegram/"]="Telegram tekshiruvi"
    )
    for ep in "${!ENDPOINTS[@]}"; do
        label="${ENDPOINTS[$ep]}"
        if [ "$ep" = "/accounts/api/check-telegram/" ]; then
            code=$(curl -s -o /dev/null -w "%{http_code}" \
                -X POST -H "Content-Type: application/json" \
                -d '{"secret_key":"youthguard-bot-secret-2024","telegram_id":1}' \
                "$BASE$ep" 2>/dev/null)
        else
            code=$(curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: Token $TOKEN" "$BASE$ep" 2>/dev/null)
        fi
        if [ "$code" = "200" ]; then
            ok "HTTP $code | $label"
        else
            err "HTTP $code | $label  ($ep)"
        fi
    done

    # So'rovnoma javobini ko'rsatish
    echo ""
    echo "  📋 Faol so'rovnoma API javobi:"
    curl -s -H "Authorization: Token $TOKEN" "https://sam-auth.uz/sorovnoma/api/active/" 2>/dev/null \
        | python3 -m json.tool 2>/dev/null | head -30 || echo "  (JSON formatlanmadi)"
fi

# ──────────────────────────────────────────────
hdr "6. SO'NGGI 5 UCHRASHUV"
docker compose exec -T web python manage.py shell << 'PYEOF'
from apps.meetings.models import Meeting
meetings = Meeting.objects.select_related('youth','rahbar').order_by('-created_at')[:5]
if not meetings:
    print("  ❌ Hali birorta uchrashuv yo'q")
else:
    print(f"  {'#':>4}  {'Yosh':20s}  {'Rahbar':15s}  {'Status':20s}  GPS   Rasm  {'Sana':16s}")
    print("  " + "─"*95)
    for m in meetings:
        gps   = "✅" if m.latitude else "❌"
        photo = "✅" if m.photo   else "❌"
        print(f"  #{m.id:<4d} {m.youth.full_name[:20]:20s}  {m.rahbar.get_full_name()[:15]:15s}  "
              f"{m.get_status_display()[:20]:20s}  {gps}    {photo}    {m.date.strftime('%d.%m.%Y %H:%M')}")
PYEOF

# ──────────────────────────────────────────────
hdr "7. BOT ULANGAN FOYDALANUVCHILAR"
docker compose exec -T web python manage.py shell << 'PYEOF'
from apps.accounts.models import CustomUser
from django.utils import timezone
from datetime import timedelta

print("  Bot bilan ulangan xodimlar:")
users = CustomUser.objects.filter(
    telegram_id__isnull=False
).exclude(role='user').select_related('organization','district')

if not users:
    print("  ❌ Hech kim bot bilan ulanmagan!")
else:
    for u in users:
        org = f" | {u.organization.name[:25]}" if u.organization else ""
        tg  = f"@{u.telegram_username}" if u.telegram_username else str(u.telegram_id)
        print(f"    {u.get_role_display():10s} | {u.get_full_name()[:25]:25s} | {tg}{org}")

print(f"\n  Telegram_id bo'sh (bot bilan bog'lanmagan) xodimlar:")
no_bot = CustomUser.objects.filter(telegram_id__isnull=True).exclude(role='user')
if no_bot:
    for u in no_bot:
        print(f"    ⚠️  {u.get_role_display():10s} | {u.get_full_name()} | tel: {u.phone}")
else:
    print("    ✅ Hammasi ulangan")
PYEOF

# ──────────────────────────────────────────────
hdr "8. XATOLAR VA LOGLAR"
echo "  📋 Web (oxirgi 5 xato):"
docker compose logs web --tail=100 2>/dev/null \
    | grep -iE "error|exception|traceback|critical|500" \
    | grep -v "healthcheck\|favicon" \
    | tail -5 \
    | sed 's/^/    /' || echo "    ✅ Xato yo'q"

echo ""
echo "  📋 Bot (oxirgi 5 xato):"
docker compose logs bot --tail=100 2>/dev/null \
    | grep -iE "error|exception|traceback|aiogram.utils.exceptions" \
    | tail -5 \
    | sed 's/^/    /' || echo "    ✅ Xato yo'q"

# ──────────────────────────────────────────────
hdr "9. DISK VA XOTIRA"
echo "  Disk:"
df -h / | awk 'NR==2 {printf "    Ishlatilgan: %s / %s (%s)\n", $3, $2, $5}'
echo "  Media fayllari:"
du -sh /var/lib/docker/volumes/*/data/media 2>/dev/null | head -3 | sed 's/^/    /'
docker compose exec -T web du -sh /app/media 2>/dev/null | sed 's/^/    Media: /'

echo ""
echo -e "${C}╔══════════════════════════════════════════════╗"
echo -e "║   Tekshiruv tugadi! ✅                        ║"
echo -e "╚══════════════════════════════════════════════╝${N}"
echo "   $(date '+%d.%m.%Y %H:%M:%S')"
echo ""
