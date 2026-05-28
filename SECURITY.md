# Security Guidelines

This document outlines security best practices for the Construction ERP system.

## 🔐 Secrets Management

### Environment Variables

**Never commit sensitive information to the repository.** Use environment variables instead:

```bash
# 1. Copy the example file
cp .env.example .env

# 2. Edit .env with YOUR OWN values (this file is in .gitignore)
# DO NOT commit .env to version control
```

### Required Secrets

| Variable | Purpose | How to Generate |
|---|---|---|
| `SECRET_KEY` | Django secret key | `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'` |
| `DATABASE_PASSWORD` | Database credentials | Generate a strong password (min 16 chars) |
| `DEBUG` | Debug mode | Set to `False` in production |

### Example `.env` file

```bash
# .env (NEVER commit this file)
SECRET_KEY=your-generated-key-here
DEBUG=False
DATABASE_URL=postgres://user:password@localhost:5432/construction_erp
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

## 👥 Default Credentials

### Demo Accounts (Development Only)

The following demo accounts are seeded with the `seed_demo_data` command for **development only**:

| Username | Role | Default Password |
|---|---|---|
| `admin` | Admin | `Demo@1234` |
| `pm_john` | Project Manager | `Demo@1234` |
| `eng_sara` | Site Engineer | `Demo@1234` |
| `qs_mike` | Quantity Surveyor | `Demo@1234` |
| `safety_ann` | Safety Officer | `Demo@1234` |
| `store_bob` | Storekeeper | `Demo@1234` |
| `viewer_tom` | Viewer | `Demo@1234` |

### ⚠️ IMPORTANT for Production

**Before deploying to production:**

1. **DO NOT use demo accounts in production**
2. **Change all default passwords immediately**
3. Run this command to remove demo data:
   ```bash
   python manage.py flush --no-input
   ```
4. Create new admin accounts with strong passwords:
   ```bash
   python manage.py createsuperuser
   ```

## 🛡️ Credential Scanning

### Pre-commit Hooks

Install `detect-secrets` to prevent credential leaks:

```bash
# Install the package
pip install detect-secrets

# Initialize scanning
detect-secrets scan > .secrets.baseline

# Install pre-commit hook
pre-commit install
```

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    args: ['scan', '--baseline', '.secrets.baseline']
    stages: [commit]
```

### GitHub Secret Scanning

1. Go to **Settings → Security → Secret scanning**
2. Enable **Secret scanning** (for public repos)
3. Enable **Push protection** to block commits with detected secrets

## 🔑 API Authentication

### Session-based (Web)
- Use Django's default session framework
- CSRF tokens are automatically handled by Django templates
- Secure cookies in production (set `SESSION_COOKIE_SECURE=True`)

### Token-based (API)
- Store API tokens securely in user profile
- Use HTTPS for all API requests
- Include token in `Authorization: Token <your_token>` header

```bash
# Example API call
curl -H "Authorization: Token your_api_token" \
     https://yourdomain.com/api/v1/projects/
```

## 📝 Database Security

### SQLite (Development)

```bash
# Ensure db.sqlite3 is in .gitignore
echo "db.sqlite3" >> .gitignore
```

### PostgreSQL (Production)

```bash
# Use strong password with special characters
DATABASE_URL=postgres://erp_user:P@ssw0rd!Secure123@db.example.com:5432/construction_erp

# Enable SSL connections
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'SSLMODE': 'require',
    }
}
```

## 🚀 Production Deployment Checklist

- [ ] Set `DEBUG = False`
- [ ] Set `SECRET_KEY` to a secure random value
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Enable `SESSION_COOKIE_SECURE = True`
- [ ] Enable `SESSION_COOKIE_HTTPONLY = True`
- [ ] Enable `CSRF_COOKIE_SECURE = True`
- [ ] Set strong database password
- [ ] Remove all demo data
- [ ] Create new admin account
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Enable monitoring and logging

## 🔍 Audit Logging

Monitor sensitive operations:

```python
# Log user authentication
AUTH_LOG_ENABLED = True

# Log all delete operations (enforced for admin only)
DELETE_LOG_ENABLED = True

# Review logs regularly
python manage.py view_auth_logs
python manage.py view_delete_logs
```

## 📞 Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email security details to: [your-security-contact@example.com]
3. Allow time for a fix before public disclosure

## 📚 Additional Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/Top10/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)

---

**Last Updated**: May 28, 2026  
**Version**: 1.0
