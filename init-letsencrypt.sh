#!/bin/sh
# ===== sam-auth.uz uchun birinchi SSL sertifikatni olish =====
# Faqat BIR MARTA, serverda deploy qilgandan keyin ishga tushiriladi:
#   chmod +x init-letsencrypt.sh && ./init-letsencrypt.sh
set -e

DOMAIN="sam-auth.uz"
EMAIL="admin@sam-auth.uz"        # <-- o'z emailingizni yozing (muddat tugashi haqida ogohlantirish keladi)
STAGING=0                        # Test uchun 1 qiling (Let's Encrypt limitiga tushmaslik uchun)

DATA_PATH="./certbot"
COMPOSE="docker compose"

if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  echo "Sertifikat allaqachon mavjud. Chiqildi."
  exit 0
fi

echo "### Tavsiya etilgan TLS parametrlari yuklanmoqda..."
mkdir -p "$DATA_PATH/conf"
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$DATA_PATH/conf/options-ssl-nginx.conf" || true
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$DATA_PATH/conf/ssl-dhparams.pem" || true

echo "### Vaqtinchalik (dummy) sertifikat yaratilmoqda..."
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
$COMPOSE run --rm --entrypoint "\
  sh -c 'mkdir -p $CERT_PATH && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout $CERT_PATH/privkey.pem \
    -out $CERT_PATH/fullchain.pem \
    -subj /CN=localhost'" certbot

echo "### Nginx ishga tushirilmoqda..."
$COMPOSE up --force-recreate -d nginx

echo "### Vaqtinchalik sertifikat o'chirilmoqda..."
$COMPOSE run --rm --entrypoint "\
  sh -c 'rm -Rf /etc/letsencrypt/live/$DOMAIN && \
  rm -Rf /etc/letsencrypt/archive/$DOMAIN && \
  rm -Rf /etc/letsencrypt/renewal/$DOMAIN.conf'" certbot

echo "### Let's Encrypt dan haqiqiy sertifikat so'ralmoqda..."
STAGING_ARG=""
if [ "$STAGING" != "0" ]; then STAGING_ARG="--staging"; fi

$COMPOSE run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $STAGING_ARG \
    --email $EMAIL \
    -d $DOMAIN -d www.$DOMAIN \
    --rsa-key-size 4096 \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot

echo "### Nginx qayta yuklanmoqda..."
$COMPOSE exec nginx nginx -s reload

echo "### TAYYOR! https://$DOMAIN endi SSL bilan ishlaydi."
