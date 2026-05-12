# Construction ERP Project Conventions

## Repo Shape

- Django project root: `config/`
- App code: `apps/<app>/`
- Templates: `templates/<app>/`
- Shared layout: `templates/base.html`, `templates/includes/navbar.html`, `templates/includes/sidebar.html`
- Shared JS/CSS: `static/js/custom.js`, `static/css/custom.css`
- Use the repo virtualenv for checks: `.\venv\Scripts\python.exe`

## UI And Template Rules

- Use Bootstrap 5 utility classes and Font Awesome icons already present in templates.
- Prefer a shared include/layout edit when the request says "all pages".
- Keep page-specific action buttons in the first header row of the page's `{% block content %}`.
- Preserve project filters when linking back from Rock/Sand pages: append `?project={{ request.GET.project }}` when available.
- Use Django `{% url %}` names instead of hardcoded internal paths.
- Avoid JavaScript-only navigation for workflow-specific buttons when a direct URL exists.

## Dashboard Rules

- Executive Dashboard is data-heavy; avoid landing-page styling.
- Do not change calculations in templates; update helper functions in the view if derived data is needed.
- Chart axis ticks can remain numeric when chart titles/tooltips include units.
- Important visible quantities should show units inline when the UI could be ambiguous.

## Material Control Rules

- Main Material/Project Controls dashboard route: `project_controls:dashboard`.
- Rock records route: `project_controls:rock_list`; Sand records route: `project_controls:sand_list`.
- Rock dashboard quantities are tons; common fields end in `_ton`.
- Sand dashboard quantities are tons; use `tons`, `tons/day`, `trips`, and `tons/trip` in visible text where useful.
- For Rock/Sand list pages, keep direct actions grouped near the title: Material Control, Dashboard, New Record, Export.

## BOQ Rules

- BOQ quantity unit lives on `BOQItem.unit`.
- Keep `contract_quantity`, `cumulative_quantity`, and `remaining_quantity` visually paired with unit where practical.
- Preferred BOQ column order when quantities are shown: item/description, quantity, unit, cumulative/progress, financials, actions.
- BOQ form layout should keep `contract_quantity` before `unit` when matching list/table order.

## Validation

Run at least:

```powershell
.\venv\Scripts\python.exe manage.py check
```

For touched app behavior, run focused tests, for example:

```powershell
.\venv\Scripts\python.exe manage.py test apps.dashboard apps.project_controls apps.boq
```

If only templates changed, also load touched templates through Django's template loader to catch syntax errors.
