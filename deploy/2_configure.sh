#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Step 2: Configure app — รันหลัง 1_server_setup.sh
# รันด้วย: bash 2_configure.sh
# ─────────────────────────────────────────────────────────────────
set -e

APP_USER="erp"
APP_DIR="/var/www/construction_erp"

echo "==> Create .env (production)"
cat > $APP_DIR/.env << 'ENVEOF'
SECRET_KEY=REPLACE_WITH_LONG_RANDOM_KEY
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production

DATABASE_URL=postgresql://erp_user:CHANGE_THIS_PASSWORD@localhost:5432/construction_erp

ALLOWED_HOSTS=187.77.141.145,yourdomain.com

SECURE_SSL_REDIRECT=False
CSRF_TRUSTED_ORIGINS=http://187.77.141.145

LOG_LEVEL=WARNING
LOG_DIR=/var/log/construction_erp

SENTRY_DSN=
ENVEOF

chown $APP_USER:$APP_USER $APP_DIR/.env
chmod 600 $APP_DIR/.env

echo "==> Run migrations"
cd $APP_DIR
sudo -u $APP_USER venv/bin/python manage.py migrate --settings=config.settings.production

echo "==> Collect static files"
sudo -u $APP_USER venv/bin/python manage.py collectstatic --noinput --settings=config.settings.production

echo "==> Compile translation messages"
sudo -u $APP_USER venv/bin/python compile_mo.py

echo "==> Create superuser (กรอกข้อมูลตามที่ต้องการ)"
sudo -u $APP_USER venv/bin/python manage.py createsuperuser --settings=config.settings.production

echo ""
echo "✓ Configuration complete!"
echo "  Next: run 3_services.sh to setup nginx + gunicorn"
