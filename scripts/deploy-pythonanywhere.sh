#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/supakorn1997/construction_erp}"
BRANCH="${BRANCH:-main}"
DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"
PYTHON="${PYTHON:-python}"
PA_USERNAME="${PA_USERNAME:-supakorn1997}"
PA_DOMAIN="${PA_DOMAIN:-supakorn1997.pythonanywhere.com}"
WSGI_FILE="${WSGI_FILE:-/var/www/supakorn1997_pythonanywhere_com_wsgi.py}"

cd "$PROJECT_DIR"

echo "==> Pulling latest code from origin/$BRANCH"
git pull origin "$BRANCH"

echo "==> Running migrations"
"$PYTHON" manage.py migrate --settings="$DJANGO_SETTINGS_MODULE"

echo "==> Collecting static files"
"$PYTHON" manage.py collectstatic --noinput --settings="$DJANGO_SETTINGS_MODULE"

echo "==> Reloading PythonAnywhere web app"
if [[ -n "${API_TOKEN:-}" ]]; then
  "$PYTHON" - <<PY
import os
import sys
import urllib.error
import urllib.request

username = os.environ.get("PA_USERNAME", "$PA_USERNAME")
domain = os.environ.get("PA_DOMAIN", "$PA_DOMAIN")
token = os.environ["API_TOKEN"]
url = f"https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain}/reload/"
request = urllib.request.Request(url, method="POST")
request.add_header("Authorization", f"Token {token}")

try:
    with urllib.request.urlopen(request, timeout=60) as response:
        print(f"Reload requested: HTTP {response.status}")
except urllib.error.HTTPError as exc:
    print(f"PythonAnywhere reload API failed: HTTP {exc.code}", file=sys.stderr)
    print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
    raise
PY
elif [[ -f "$WSGI_FILE" ]]; then
  touch "$WSGI_FILE"
  echo "Reload requested by touching $WSGI_FILE"
else
  echo "No API_TOKEN and WSGI file not found at $WSGI_FILE"
  echo "Open the PythonAnywhere Web tab and click Reload."
fi

echo "==> Deploy complete"
