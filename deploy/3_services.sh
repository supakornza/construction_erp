#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Step 3: Setup nginx + gunicorn systemd service
# รันด้วย: bash 3_services.sh
# ─────────────────────────────────────────────────────────────────
set -e

APP_DIR="/var/www/construction_erp"

echo "==> Install gunicorn systemd service"
cp $APP_DIR/deploy/construction_erp.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable construction_erp
systemctl start construction_erp
systemctl status construction_erp --no-pager

echo "==> Install nginx config"
cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/construction_erp
ln -sf /etc/nginx/sites-available/construction_erp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "==> Open firewall"
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

echo ""
echo "✓ Services running!"
echo "  Site: http://187.77.141.145"
echo ""
echo "  ถ้ามี domain ให้รัน:"
echo "  certbot --nginx -d yourdomain.com"
