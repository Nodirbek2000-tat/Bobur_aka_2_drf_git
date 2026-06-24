#!/bin/sh
set -e

echo "==> Postgres kutilmoqda..."
until python -c "import psycopg2, os; psycopg2.connect(dbname=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'], host=os.environ['POSTGRES_HOST'], port=os.environ.get('POSTGRES_PORT','5432'))" 2>/dev/null; do
  echo "   ...db hali tayyor emas, 2s kutamiz"
  sleep 2
done
echo "==> Postgres tayyor!"

echo "==> Migratsiyalar..."
python manage.py migrate --noinput

echo "==> Statik fayllar..."
python manage.py collectstatic --noinput

# Birinchi ishga tushishda superuser yaratish (agar env berilgan bo'lsa)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  echo "==> Superuser tekshirilmoqda..."
  python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
u = '$DJANGO_SUPERUSER_USERNAME'
if not U.objects.filter(username=u).exists():
    U.objects.create_superuser(u, '${DJANGO_SUPERUSER_EMAIL:-admin@sam-auth.uz}', '$DJANGO_SUPERUSER_PASSWORD', role='super_admin')
    print('Superuser yaratildi:', u)
else:
    print('Superuser allaqachon mavjud:', u)
"
fi

echo "==> Gunicorn ishga tushmoqda..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
