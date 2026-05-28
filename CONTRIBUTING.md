# Contributing to Construction ERP

Thank you for your interest in contributing! Please follow these guidelines.

## 🔐 Security First

### Never Commit Secrets

**CRITICAL**: Do not commit sensitive information:

- API keys or tokens
- Database credentials
- SSH keys or private keys
- AWS/cloud credentials
- Third-party service credentials
- Default passwords or demo credentials

**All sensitive data should be:**
1. Added to `.env` (which is in `.gitignore`)
2. Set as environment variables in your deployment
3. Managed through secure secret management tools

### Pre-commit Hooks

Before committing, install pre-commit hooks to catch secrets:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# (Optional) Run against all files to check existing history
pre-commit run --all-files
```

This will automatically scan for secrets before each commit.

## 📋 Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/supakornza/construction_erp.git
cd construction_erp
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Additional dev tools
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your local settings
```

### 5. Initialize database

```bash
python manage.py migrate
python manage.py seed_demo_data  # Loads demo accounts for development
```

### 6. Run development server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ and log in with `admin / Demo@1234`

## 🎯 Code Standards

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where possible
- Maximum line length: 120 characters
- Use Black for formatting (runs via pre-commit)

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Example:**
```
feat(daily-reports): add email notification for approvals

- Implement email template for report approvals
- Add Celery task for async email sending
- Include project and report details in email

Closes #123
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test apps.daily_reports.tests

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Requirements

- All new features must include tests
- Aim for >80% code coverage
- Mock external services

## 📝 Pull Request Process

1. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following code standards

3. **Test thoroughly**:
   ```bash
   python manage.py test
   pre-commit run --all-files
   ```

4. **Commit with meaningful messages**

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** with:
   - Clear description of changes
   - Reference to related issues (#123)
   - Screenshots for UI changes
   - Test results

7. **Address review feedback** promptly

## 📚 Documentation

- Update README.md if adding features
- Add docstrings to functions and classes
- Document API endpoints if creating new ones
- Update SECURITY.md if changing security-related code

## 🐛 Bug Reports

Report bugs by opening an issue with:

- **Title**: Clear, specific bug description
- **Reproduction steps**: Exact steps to reproduce
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, Django version
- **Screenshots**: If applicable

## ✨ Feature Requests

Suggest features by opening an issue with:

- **Title**: Feature description
- **Use case**: Why this feature is needed
- **Proposed solution**: How it should work
- **Alternatives**: Any alternative approaches

## 📞 Questions?

- Check existing issues and discussions
- Review documentation in SECURITY.md
- Ask in pull request comments

---

**Thank you for contributing! 🚀**
