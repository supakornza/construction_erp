# Construction ERP System

A Django web application for managing construction site operations — daily reports, manpower, equipment, materials, BOQ progress, safety, procurement, documents, and marine project controls.

---

## Features

- **Projects** – Multi-project management with status tracking, stakeholders, and work areas
- **Daily Reports** – Structured daily site reports with approval workflow (Draft → Submitted → Approved/Rejected)
- **Manpower** – Daily headcount tracking by category with 30-day histogram charts
- **Equipment** – Fleet management with daily utilization records
- **Materials** – Delivery tracking, usage records, and real-time stock balance
- **Procurement** – Purchase Request (PR) → Purchase Order (PO) workflow with supplier management
- **BOQ & Progress** – Bill of Quantities with cumulative progress and earned value tracking
- **Safety** – Toolbox meetings, safety inspections, incident reports, and JSEA records
- **Documents** – Document register with revision history
- **Project Controls** – Marine construction module: rock/sand daily summaries with barge placements, sand allocation calculator, revetment progress tracking, 14-day recovery plans, Recovery Action Plans (RAP) with approval workflow, logistics scenario simulator, and Excel/PDF imports
- **Dashboard** – KPI cards, Chart.js charts, and project progress overview
- **REST API** – Full DRF API at `/api/v1/` for all modules
- **Exports** – PDF daily reports and RAP (ReportLab); Excel BOQ/materials/safety/rock/sand/revetment/RAP (openpyxl)
- **Role-Based Access** – 7 roles; delete operations restricted to Admin only

---

## Quick Start

### Windows: double-click launcher

For the simplest local startup on Windows, double-click:

```text
Construction-ERP-Windows.bat
```

The launcher checks Python and the virtual environment, installs missing application packages, validates the Django project, starts the server, and opens `http://127.0.0.1:8000/` in the default browser. Keep the launcher window open while using the application; press `Ctrl+C` or close it to stop the local server.

It preserves an existing SQLite database. On a clean copy with no `db.sqlite3`, it creates the database by applying migrations but does not add demo users or demo data automatically.

### Terminal setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY

# 4. Initialize database and seed demo data
python manage.py migrate
python manage.py seed_demo_data

# 5. Start development server
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in with `admin / Demo@1234`

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | `django-insecure-...` |
| `DEBUG` | Debug mode | `True` / `False` |
| `DATABASE_URL` | Database connection URL | `sqlite:///db.sqlite3` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |

---

## User Roles

| Username | Role | Permissions |
|---|---|---|
| `admin` | Admin | Full access including delete operations |
| `pm_john` | Project Manager | Approve reports, full module access |
| `eng_sara` | Site Engineer | Create/edit daily reports, manpower, equipment |
| `qs_mike` | Quantity Surveyor | BOQ, materials, procurement |
| `safety_ann` | Safety Officer | Safety module full access |
| `store_bob` | Storekeeper | Materials and deliveries |
| `viewer_tom` | Viewer | Read-only access to all modules |

*All demo accounts use password: `Demo@1234`*

Delete buttons are visible and functional only for `admin` role and superusers — enforced at both the template and view layer.

---

## Permissions

| Action | Admin | Project Manager | Site Engineer | QS | Safety | Storekeeper | Viewer |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| View all modules | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create / Edit records | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Approve reports / RAP | ✓ | ✓ | — | — | — | — | — |
| Delete records | ✓ | — | — | — | — | — | — |

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/v1/projects/` | List/create projects |
| `GET /api/v1/daily-reports/` | Daily reports |
| `GET /api/v1/manpower/records/` | Manpower records |
| `GET /api/v1/equipment/records/` | Equipment records |
| `GET /api/v1/materials/deliveries/` | Material deliveries |
| `GET /api/v1/materials/stock/` | Stock balance (requires `?project_id=`) |
| `GET /api/v1/boq/items/` | BOQ items with computed progress |
| `GET /api/v1/boq/progress/` | Daily progress records |
| `GET /api/v1/safety/inspections/` | Safety inspections |
| `GET /api/v1/documents/` | Document register |
| `GET /api/v1/dashboard/chart-data/` | Chart data for dashboard |

Authentication: Session or Basic Auth. All endpoints require authentication.

---

## Export Features

| Export | URL | Format |
|---|---|---|
| Daily Report PDF | `/daily-reports/<id>/pdf/` | PDF (ReportLab) |
| Material Deliveries | `/reports/project/<id>/materials/excel/` | Excel (.xlsx) |
| BOQ Progress | `/reports/project/<id>/boq/excel/` | Excel (.xlsx) |
| Safety Observations | `/reports/project/<id>/safety/excel/` | Excel (.xlsx) |
| Rock Summary | `/project-controls/rock/export/<project_id>/` | Excel (.xlsx) |
| Rock Daily PDF | `/project-controls/rock/<id>/pdf/` | PDF (ReportLab) |
| Sand Summary | `/project-controls/sand/export/<project_id>/` | Excel (.xlsx) |
| Revetment Progress | `/project-controls/revetment/export/<project_id>/` | Excel (.xlsx) |
| Recovery Action Plan | `/project-controls/recovery/rap/<id>/export/` | Excel (.xlsx) |
| Recovery Action Plan PDF | `/project-controls/recovery/rap/<id>/pdf/` | PDF (ReportLab) |

---

## Project Controls Module

Marine-construction focused module mounted at `/project-controls/`:

| Section | URL | Purpose |
|---|---|---|
| Dashboard | `/project-controls/` | Module landing with KPIs across rock, sand, revetment, recovery |
| Rock Daily | `/project-controls/rock/` | TCT/placed tonnage per day with barge placements, accumulators, stock balance |
| Sand Daily | `/project-controls/sand/` | TCT / MTP3 / other sources, offshore/onshore placement, remaining stock |
| Sand Allocation | `/project-controls/sand/allocation/` | Splits total quantity & trips by TCT/MTP3 percentages |
| Revetment | `/project-controls/revetment/` | Station × activity matrix with quantities, statuses, and inspections |
| 14-Day Recovery Plan | `/project-controls/recovery/plans/` | Rolling 14-day planned vs actual material recovery with inline day table |
| Recovery Action Plan | `/project-controls/recovery/rap/` | NTP-linked action items with Draft → Submitted → Approved workflow |
| Logistics Scenarios | `/project-controls/logistics/` | Truck cycle-time calculator (trips/day, tonnage/day) with comparison view |
| Imports | `/project-controls/import/` | Upload Excel/PDF rock-summary, sand-summary, RAP and revetment files |

---

## Tech Stack

- **Backend**: Django 6.0.5 + Django REST Framework 3.17.1
- **Python**: 3.14 (note: `psycopg2-binary` is not yet compatible with 3.14 — use SQLite in dev)
- **Database**: SQLite (dev) / PostgreSQL (prod, on Python ≤3.13)
- **Frontend**: Bootstrap 5.3 + Chart.js 4 + Font Awesome 6
- **Forms**: django-crispy-forms 2.6 + crispy-bootstrap5 2024.10
- **PDF**: ReportLab 4.5
- **Excel**: openpyxl 3.1.5
- **Static Files**: WhiteNoise 6.12
- **Server**: gunicorn 26.0 (prod)

---

## Roadmap

- [ ] Multi-project dashboard with Gantt chart
- [ ] Email notifications for report approvals
- [ ] Mobile-responsive PWA for site use
- [ ] Integration with GPS/IoT equipment tracking
- [ ] Advanced analytics and custom report builder
- [ ] Multi-language support (Thai/English)
- [ ] Biometric attendance integration
