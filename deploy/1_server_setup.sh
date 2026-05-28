#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Step 1: Server Setup — รันครั้งเดียวในฐานะ root
# รันด้วย: bash 1_server_setup.sh
# ─────────────────────────────────────────────────────────────────
set -e

APP_USER="erp"
APP_DIR="/var/www/construction_erp"
REPO="https://github.com/supakornza/construction_erp.git"

echo "==> Update system"
apt-get update && apt-get upgrade -y

echo "==> Install dependencies"
apt-get install -y \
    python3 python3-pip python3-venv \
    postgresql postgresql-contrib \
    nginx \
    git \
    gettext \
    curl \
    certbot python3-certbot-nginx

echo "==> Create app user"
id -u $APP_USER &>/dev/null || useradd -m -s /bin/bash $APP_USER

echo "==> Create app directory"
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

echo "==> Create log directory"
mkdir -p /var/log/construction_erp
chown $APP_USER:$APP_USER /var/log/construction_erp

echo "==> Setup PostgreSQL"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='erp_user'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER erp_user WITH PASSWORD 'CHANGE_THIS_PASSWORD';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='construction_erp'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE construction_erp OWNER erp_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE construction_erp TO erp_user;"

echo "==> Clone project"
sudo -u $APP_USER git clone $REPO $APP_DIR || \
    (cd $APP_DIR && sudo -u $APP_USER git pull)

echo "==> Create virtual environment"
sudo -u $APP_USER python3 -m venv $APP_DIR/venv

echo "==> Install Python packages"
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

echo ""
echo "✓ Server setup complete!"
echo "  Next: copy deploy/2_configure.sh and fill in .env then run it"
