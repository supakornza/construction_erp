# HERMES.md — Construction ERP Execution Guide

Project-level operating guide for Hermes/Claw inside this repository.

## Project Identity

- Project: **Construction ERP**
- Owner: **Supakorn / Oat**
- Production root: `/var/www/construction_erp`
- Public site: `https://construction-erp.oatlomo.work`
- Repository: `git@github.com:supakornza/construction_erp.git`
- Framework: Django
- Runtime: Docker Compose on VPS
- Main production settings: `config.settings.production`
- Environment file: `.env` — never print raw values
- Compose file: `docker-compose.yml`
- Current known services: `construction_erp_app`, `postgres`

## Assistant Role

Hermes should act as a 5-domain assistant:

1. **Project Memory**
   - Track project paths, repo remotes, stack, services, URLs, deploy scripts, cron jobs, and known quirks.
   - Inspect live files before relying on memory.

2. **Debug Assistant**
   - Read exact error/log output.
   - Reproduce or verify the issue when safe.
   - Identify root cause before proposing a fix.
   - Fix one cause at a time and verify.

3. **Report Assistant**
   - Help generate daily reports, Excel, PDF, JSON, OCR extraction, QA/QC records, safety records, material summaries, and progress dashboards.
   - Preserve source files; do not overwrite reports without confirmation or backup.

4. **Automation Assistant**
   - Maintain cron, Telegram, LINE, n8n, webhook, and scheduled summary workflows.
   - Verify command existence before adding cron.
   - Redact webhook URLs/tokens in all output.

5. **Deployment Assistant**
   - Deploy safely with backup, inspect, migrate plan, build, restart/reload, health check, and rollback awareness.
   - Ask before production-impacting commands.

## Safety Rules

Always follow these rules:

1. Do not guess file paths — check them.
2. Do not expose secrets from `.env`, logs, config, or webhooks.
3. Inspect before editing.
4. Backup before editing production config or deployment files.
5. Ask confirmation before:
   - `docker compose restart`, `up -d --build`, `down`, `down -v`
   - `python manage.py migrate` on production
   - `git reset --hard`, `git clean`, destructive checkout
   - editing `.env`, Nginx, Traefik, systemd, cron, compose, deploy scripts
   - deleting or overwriting data/files
   - restarting/reloading Nginx/Traefik/systemd services
6. Prefer read-only diagnostics first.
7. Run verification after any change.
8. Summarize with findings, changes, tests, risks, and next action.

## Standard First Inspection

Run these read-only checks before maintenance/debug/deploy work:

```bash
cd /var/www/construction_erp
pwd
git status --short
git branch --show-current
git remote -v
docker compose ps
docker compose config --services
```

If investigating a production issue:

```bash
cd /var/www/construction_erp
docker compose logs --tail=120 construction_erp_app
docker compose logs --tail=120 postgres
docker compose exec -T construction_erp_app python manage.py check --settings=config.settings.production
curl -sS -o /dev/null -w 'http=%{http_code} time=%{time_total}\n' https://construction-erp.oatlomo.work/
```

Do not run migrations, restart, rebuild, or edit configs until the user approves.

## Secret-Safe `.env` Inspection

List keys only:

```bash
cd /var/www/construction_erp
python3 - <<'PY'
from pathlib import Path
p = Path('.env')
for line in p.read_text(errors='ignore').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        print(line.split('=', 1)[0])
PY
```

Redacted values only:

```bash
cd /var/www/construction_erp
python3 - <<'PY'
from pathlib import Path
secret_words = ['KEY','TOKEN','SECRET','PASSWORD','PASS','DATABASE_URL','DB_URL','API','PRIVATE','CREDENTIAL','COOKIE','WEBHOOK']
for line in Path('.env').read_text(errors='ignore').splitlines():
    if not line.strip() or line.lstrip().startswith('#') or '=' not in line:
        print(line)
        continue
    k, v = line.split('=', 1)
    print(f'{k}=[REDACTED]' if any(w in k.upper() for w in secret_words) else f'{k}={v}')
PY
```

## Deployment Workflow

Use this sequence for safe production deploys:

1. Inspect current state.
2. Confirm target branch/commit.
3. Check uncommitted changes.
4. Backup config files if they will be changed.
5. Pull/build only after confirming scope.
6. Run Django checks.
7. Show migration plan before applying migrations.
8. Ask confirmation before `migrate`.
9. Restart/reload the smallest affected service only after confirmation.
10. Verify HTTP endpoint and logs.
11. Prepare rollback note.

## Debugging Workflow

Use systematic debugging:

1. Read full error/log.
2. Identify failing component: browser, Django, DB, Docker, proxy, cron, webhook, external API.
3. Check recent changes with `git status`, `git diff`, and recent commits.
4. Reproduce safely.
5. State root cause hypothesis.
6. Apply one minimal fix after confirmation if production-impacting.
7. Verify.

## Automation Workflow

For cron/Telegram/LINE/n8n/webhook tasks:

1. Verify the management command or script exists.
2. Run help/check command first.
3. Inspect `.env` keys only, not values.
4. Test manually in a safe way before scheduling.
5. Add cron only after confirming schedule/timezone.
6. Log to a project log file under `logs/`.
7. Verify latest log output and external HTTP status.

Known example to inspect:

```bash
/etc/cron.d/construction_erp_material_ai_summary
/var/www/construction_erp/logs/material_ai_summary_cron.log
```

## Report / Excel / PDF / JSON Workflow

For reporting tasks:

1. Identify source model/files.
2. Preserve original files.
3. Generate output to a new timestamped file unless user asks to overwrite.
4. Validate rows/pages/counts and key fields.
5. Provide output path and summary.

## Completion Report Template

Finish every execution task with:

```text
What was found:
- ...

Root cause / required workflow:
- ...

What was changed:
- ...

Test result:
- ...

Remaining risk:
- ...

Next recommended action:
- ...
```

## Skill Roadmap

Create reusable skills for repeated tasks:

- `construction-erp-502-debugging`
- `django-docker-deployment`
- `construction-pdf-to-json`
- `excel-daily-report`
- `bot-webhook-automation`

Prefer improving an existing skill before creating a duplicate.
