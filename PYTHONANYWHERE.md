# Deploy to PythonAnywhere

This project is already on GitHub:

```text
https://github.com/supakornza/construction_erp
```

## 1. Clone on PythonAnywhere

Open a PythonAnywhere **Bash** console:

Do not use a Python console. If you see `>>>`, type `exit()` first, then open a new **Bash** console from the PythonAnywhere Consoles page.

```bash
cd ~
git clone https://github.com/supakornza/construction_erp.git
cd construction_erp
```

## 2. Create Virtualenv

Django 6 requires Python 3.12 or newer. Use Python 3.12 or 3.13 on PythonAnywhere:

```bash
mkvirtualenv --python=/usr/bin/python3.13 construction_erp_env
pip install -r requirements.txt
```

If Python 3.13 is not available on your PythonAnywhere account, use:

```bash
mkvirtualenv --python=/usr/bin/python3.12 construction_erp_env
```

## 3. Create Production `.env`

Create `/home/supakornza/construction_erp/.env`:

```bash
nano .env
```

Example:

```env
SECRET_KEY=replace-with-a-long-random-secret-key
DEBUG=False
DATABASE_URL=sqlite:////home/supakornza/construction_erp/db.sqlite3
ALLOWED_HOSTS=supakornza.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://supakornza.pythonanywhere.com
SECURE_SSL_REDIRECT=True
```

If you use a custom domain, add it to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

## 4. Migrate and Seed

```bash
python manage.py migrate --settings=config.settings.production
python manage.py seed_demo_data --settings=config.settings.production
python manage.py collectstatic --settings=config.settings.production
```

Demo login after seeding:

```text
admin / Demo@1234
```

## 5. Create Web App

On PythonAnywhere:

1. Go to **Web**
2. Add a new web app
3. Choose **Manual configuration**
4. Choose the same Python version as the virtualenv, for example Python 3.12
5. Set virtualenv:

```text
/home/supakornza/.virtualenvs/construction_erp_env
```

Set source code / working directory:

```text
/home/supakornza/construction_erp
```

## 6. WSGI File

Edit the WSGI file from the PythonAnywhere Web tab, usually:

```text
/var/www/supakornza_pythonanywhere_com_wsgi.py
```

Use:

```python
import os
import sys

path = '/home/supakornza/construction_erp'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## 7. Static and Media Mappings

In the PythonAnywhere Web tab, add:

```text
URL: /static/
Directory: /home/supakornza/construction_erp/staticfiles
```

Optional, for uploaded files:

```text
URL: /media/
Directory: /home/supakornza/construction_erp/media
```

Reload the web app after saving.

## 8. Update Later

After pushing new code to GitHub:

```bash
cd /home/supakornza/construction_erp
git pull
pip install -r requirements.txt
python manage.py migrate --settings=config.settings.production
python manage.py collectstatic --settings=config.settings.production
```

Then click **Reload** on the PythonAnywhere Web tab.
