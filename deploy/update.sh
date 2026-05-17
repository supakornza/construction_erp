#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Update script — รันทุกครั้งที่ต้องการ deploy โค้ดใหม่
# รันด้วย: bash /var/www/construction_erp/deploy/update.sh
# ─────────────────────────────────────────────────────────────────
set -e

APP_DIR="/var/www/construction_erp"
APP_USER="erp"

echo "==> Pull latest code"
cd $APP_DIR
sudo -u $APP_USER git pull origin main

echo "==> Install/update packages"
sudo -u $APP_USER venv/bin/pip install -r requirements.txt

echo "==> Run migrations"
sudo -u $APP_USER venv/bin/python manage.py migrate --settings=config.settings.production

echo "==> Collect static"
sudo -u $APP_USER venv/bin/python manage.py collectstatic --noinput --settings=config.settings.production

echo "==> Compile translations"
sudo -u $APP_USER venv/bin/python compile_mo.py

echo "==> Restart gunicorn"
systemctl restart construction_erp

echo "✓ Update complete! Site is live."
