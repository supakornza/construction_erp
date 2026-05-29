#!/bin/bash
# Deploy script for Construction ERP on Ubuntu VPS
# Run as root: bash deploy_vps.sh

set -e

APP_DIR="/var/www/construction_erp"
VENV_DIR="$APP_DIR/venv"
DJANGO_SETTINGS="config.settings.production"
GUNICORN_WORKERS=3
APP_PORT=8000

echo "=== Construction ERP VPS Deployment ==="

# 1. System packages
echo "[1/8] Installing system packages..."
apt-get update -q
apt-get install -y -q python3 python3-pip python3-venv nginx git curl gettext

# 2. Create app directory and copy files
echo "[2/8] Setting up app directory..."
mkdir -p "$APP_DIR"
rsync -a --exclude='venv' --exclude='.git' --exclude='__pycache__' \
      --exclude='*.pyc' --exclude='.env' --exclude='db.sqlite3' \
      --exclude='.claude' --exclude='staticfiles' \
      /tmp/construction_erp/ "$APP_DIR/"

# 3. Virtual environment + dependencies
echo "[3/8] Installing Python dependencies..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt" -q

# 4. Environment file
echo "[4/8] Configuring environment..."
if [ ! -f "$APP_DIR/.env" ]; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    cat > "$APP_DIR/.env" <<EOF
SECRET_KEY=$SECRET
DEBUG=False
DATABASE_URL=sqlite:////var/www/construction_erp/db.sqlite3
ALLOWED_HOSTS=187.77.141.145,localhost
SECURE_SSL_REDIRECT=False
CSRF_TRUSTED_ORIGINS=http://187.77.141.145
LOG_LEVEL=WARNING
LOG_DIR=/var/log/construction_erp
SENTRY_DSN=
EOF
    echo "  .env created (edit /var/www/construction_erp/.env to customize)"
else
    echo "  .env already exists, skipping"
fi

# 5. Django setup
echo "[5/8] Running migrations and collecting static files..."
cd "$APP_DIR"
export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS"
"$VENV_DIR/bin/python" manage.py migrate --noinput
"$VENV_DIR/bin/python" manage.py compilemessages --ignore=venv 2>/dev/null || true
"$VENV_DIR/bin/python" manage.py collectstatic --noinput -v 0

# 6. Permissions
echo "[6/8] Setting permissions..."
mkdir -p /var/log/construction_erp
chown -R www-data:www-data "$APP_DIR"
chown -R www-data:www-data /var/log/construction_erp
chmod 750 "$APP_DIR"

# 7. Systemd service
echo "[7/8] Creating systemd service..."
cat > /etc/systemd/system/construction_erp.service <<EOF
[Unit]
Description=Construction ERP Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
Environment="DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS"
ExecStart=$VENV_DIR/bin/gunicorn config.wsgi:application \
    --workers $GUNICORN_WORKERS \
    --bind 127.0.0.1:$APP_PORT \
    --access-logfile /var/log/construction_erp/gunicorn_access.log \
    --error-logfile /var/log/construction_erp/gunicorn_error.log \
    --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable construction_erp
systemctl restart construction_erp

# 8. Nginx config
echo "[8/8] Configuring Nginx..."
cat > /etc/nginx/sites-available/construction_erp <<EOF
server {
    listen 80;
    server_name 187.77.141.145;

    client_max_body_size 50M;

    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $APP_DIR/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/construction_erp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "=== Deployment complete! ==="
echo "App running at: http://187.77.141.145"
echo ""
echo "Useful commands:"
echo "  systemctl status construction_erp   # check service status"
echo "  journalctl -u construction_erp -f   # live logs"
echo "  tail -f /var/log/construction_erp/gunicorn_error.log"
echo ""
echo "Create admin user:"
echo "  cd $APP_DIR && DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS $VENV_DIR/bin/python manage.py createsuperuser"
