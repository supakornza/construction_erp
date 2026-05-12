---
name: construction-erp-review
description: Project-specific guidance for the Construction ERP Django app. Use when Codex reviews, edits, or verifies this repo's Django views/forms/templates, Executive Dashboard, Project Controls dashboard, Rock/Sand material-control workflows, BOQ screens, units/quantity presentation, navigation, or focused tests.
---

# Construction ERP Review

## Quick Start

Treat this repo as a Django template-first business app. Before editing, inspect the relevant view, form, model, URL, and template together; most behavior is split across `apps/*` and `templates/*`.

Use existing project patterns:
- Prefer template/view changes over schema changes unless the request explicitly needs data model changes.
- Preserve current Bootstrap 5, Font Awesome, crispy-forms, and Django template idioms.
- Keep user-facing changes scoped to the requested workflow; avoid broad visual redesigns.
- After edits, run `.\venv\Scripts\python.exe manage.py check` and focused tests for touched apps.

## Common Workflows

For dashboard or UI changes:
- Check `templates/base.html`, `templates/includes/navbar.html`, and `static/js/custom.js` for shared behavior before editing every page.
- For Executive Dashboard, read `apps/dashboard/views.py` plus `templates/dashboard/index.html`.
- For Rock/Sand dashboards and records, read `apps/project_controls/views.py`, `apps/project_controls/models.py`, and the matching `templates/project_controls/{rock,sand}/...` template.

For BOQ changes:
- Read `apps/boq/models.py`, `apps/boq/forms.py`, `apps/boq/views.py`, and `templates/boq/*.html`.
- Keep BOQ quantity, unit, cumulative, earned value, and percent-complete behavior aligned across list, form, progress, and dashboard tables.

For review/security tasks:
- Lead with concrete findings tied to file/line references.
- Check permission-sensitive actions, delete forms, role checks, CSRF, project filters, date filters, and export links.
- Prefer finding regressions in workflow behavior over style-only comments.

## References

Read `references/project-conventions.md` when working on dashboard layout, Material Control, BOQ, navigation, units, validation, or test strategy.
