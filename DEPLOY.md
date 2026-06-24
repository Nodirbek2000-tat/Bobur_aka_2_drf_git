# YouthGuard — Serverga deploy qilish (sam-auth.uz)

## 1. Talablar
Server (Ubuntu 22.04+ tavsiya etiladi) da:
- Docker va Docker Compose o'rnatilgan bo'lishi kerak
- `sam-auth.uz` va `www.sam-auth.uz` domenlari serverning IP manziliga (DNS A-record) yo'naltirilgan bo'lishi shart (SSL shu uchun)

## 2. Loyihani serverga ko'chirish
```bash
git clone <repo>  # yoki fayllarni scp bilan ko'chiring
cd Bobur_aka_2_drf
```

## 3. .env.production ni to'ldirish
`.env.production` faylini oching va quyidagilarni o'zgartiring:
- `SECRET_KEY` — uzun tasodifiy satr
- `POSTGRES_PASSWORD` — kuchli parol
- `DJANGO_SUPERUSER_PASSWORD` — admin paroli
- `init-letsencrypt.sh` ichida `EMAIL=` ni o'z emailingizga o'zgartiring

## 4. Konteynerlarni qurish va ishga tushirish
```bash
docker compose build
docker compose up -d db web
```

## 5. Birinchi SSL sertifikatni olish (faqat bir marta)
```bash
chmod +x init-letsencrypt.sh
./init-letsencrypt.sh
```
Bu skript dummy sertifikat yaratadi, nginx ni ishga tushiradi, keyin
Let's Encrypt dan haqiqiy sertifikat oladi.

## 6. Hammasini ishga tushirish
```bash
docker compose up -d
```

Endi **https://sam-auth.uz** ishlaydi.

---

## Ma'lumotlar saqlanishi (MUHIM)
Postgres ma'lumotlari `postgres_data` nomli **volume** da saqlanadi.
Shuning uchun:
- `docker compose down` — ma'lumot SAQLANADI
- `docker compose pull && docker compose up -d` — ma'lumot SAQLANADI
- `git pull` + qayta build — ma'lumot SAQLANADI

Ma'lumot faqat quyidagi buyruq bilan **o'chadi** (ehtiyot bo'ling!):
```bash
docker compose down -v   # -v volume larni ham o'chiradi — ISHLATMANG!
```

## SSL avtomatik yangilanishi
`certbot` konteyneri har 12 soatda sertifikatni tekshirib, kerak bo'lsa
avtomatik yangilaydi. Hech narsa qilish shart emas.

## Foydali buyruqlar
```bash
docker compose logs -f web      # Django loglari
docker compose logs -f nginx    # Nginx loglari
docker compose restart web      # Faqat web ni qayta ishga tushirish
docker compose exec web python manage.py createsuperuser  # Qo'lda admin
```

## Ma'lumotlar bazasini zaxiralash (backup)
```bash
docker compose exec db pg_dump -U youthguard youthguard > backup_$(date +%F).sql
```
Tiklash:
```bash
cat backup.sql | docker compose exec -T db psql -U youthguard youthguard
```
