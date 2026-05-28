"""
Export all ERP pages as full-page PNG screenshots using Playwright.

Usage:
    python scripts/export_pages.py [--base-url http://127.0.0.1:8000] [--out screenshots]

Requirements:
    pip install playwright
    python -m playwright install chromium
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

# ── Configuration ─────────────────────────────────────────────────────────────
DEFAULT_BASE = "http://127.0.0.1:8000"
DEFAULT_OUT  = "screenshots"
LOGIN_USER   = "admin"
LOGIN_PASS   = "admin1234"
VIEWPORT     = {"width": 1440, "height": 900}
WAIT_MS      = 1500   # ms to wait after navigation for charts/JS to render


# ── Page definitions ──────────────────────────────────────────────────────────
# (slug, path, label)  — slug used as filename
def build_pages(pks: dict) -> list[tuple[str, str, str]]:
    p = pks
    return [
        # Dashboard
        ("01_dashboard",          "/",                                        "Dashboard"),

        # Monitoring
        ("02_tide_monitor",       "/tide-monitor/",                           "Tide Monitor"),
        ("03_turbidity_monitor",  "/turbidity-monitor/",                      "Turbidity Monitor"),

        # Projects
        ("04_project_list",       "/projects/",                               "Projects – List"),
        ("05_project_detail",     f"/projects/{p['project']}/",               "Project – Detail"),

        # Daily Reports
        ("06_daily_report_list",  "/daily-reports/",                          "Daily Reports – List"),
        ("07_daily_report_detail",f"/daily-reports/{p['daily_report']}/",     "Daily Report – Detail"),

        # Manpower
        ("08_manpower_dashboard", "/manpower/dashboard/",                     "Manpower – Dashboard"),
        ("09_manpower_list",      "/manpower/",                               "Manpower – Records"),
        ("10_manpower_histogram", "/manpower/histogram/",                     "Manpower – Histogram"),

        # Equipment
        ("11_equipment_list",     "/equipment/",                              "Equipment – List"),
        ("12_equipment_detail",   f"/equipment/{p['equipment']}/",            "Equipment – Detail"),
        ("13_equipment_records",  "/equipment/records/",                      "Equipment – Daily Records"),

        # Materials
        ("14_materials_dashboard","/materials/dashboard/",                    "Materials – Dashboard"),
        ("15_materials_list",     "/materials/",                              "Materials – List"),
        ("16_materials_delivery", "/materials/deliveries/",                   "Materials – Deliveries"),
        ("17_materials_stock",    "/materials/stock/",                        "Materials – Stock Balance"),

        # Procurement
        ("18_suppliers",          "/procurement/suppliers/",                  "Procurement – Suppliers"),
        ("19_pr_list",            "/procurement/pr/",                         "Procurement – Purchase Requests"),
        ("20_pr_detail",          f"/procurement/pr/{p['purchase_request']}/","Procurement – PR Detail"),
        ("21_po_list",            "/procurement/po/",                         "Procurement – Purchase Orders"),
        ("22_po_detail",          f"/procurement/po/{p['purchase_order']}/",  "Procurement – PO Detail"),

        # BOQ & Progress
        ("23_boq_list",           "/boq/",                                    "BOQ – Item List"),
        ("24_boq_progress",       "/boq/progress/",                           "BOQ – Progress Records"),
        ("25_boq_claims",         "/boq/claims/",                             "BOQ – Payment Claims"),
        ("26_boq_claim_detail",   f"/boq/claims/{p['payment_claim']}/",       "BOQ – Claim Detail"),

        # Project Controls
        ("27_pc_dashboard",       "/project-controls/",                       "Project Controls – Dashboard"),
        ("28_rock_dashboard",     "/project-controls/rock/dashboard/",        "Rock – Dashboard"),
        ("29_rock_list",          "/project-controls/rock/",                  "Rock – Records"),
        ("30_rock_detail",        f"/project-controls/rock/{p['rock']}/",     "Rock – Record Detail"),
        ("31_sand_dashboard",     "/project-controls/sand/dashboard/",        "Sand – Dashboard"),
        ("32_sand_list",          "/project-controls/sand/",                  "Sand – Records"),
        ("33_sand_detail",        f"/project-controls/sand/{p['sand']}/",     "Sand – Record Detail"),
        ("34_sand_allocation",    "/project-controls/sand/allocation/",       "Sand – Allocation"),
        ("35_revetment_dashboard","/project-controls/revetment/dashboard/",   "Revetment – Dashboard"),
        ("36_revetment_setup",    "/project-controls/revetment/setup/",       "Revetment – Setup"),
        ("37_revetment_list",     "/project-controls/revetment/",             "Revetment – Records"),
        ("38_recovery_plans",     "/project-controls/recovery/plans/",        "Recovery Plans – List"),
        ("39_recovery_plan_detail",f"/project-controls/recovery/plans/{p['recovery_plan']}/","Recovery Plan – Detail"),
        ("40_rap_list",           "/project-controls/recovery/rap/",          "Recovery Action Plans – List"),
        ("41_rap_detail",         f"/project-controls/recovery/rap/{p['rap']}/","Recovery Action Plan – Detail"),
        ("42_rap_dashboard",      "/project-controls/recovery/rap/dashboard/","Recovery Action Plans – Dashboard"),
        ("43_action_plans",       "/project-controls/action-plans/",          "Project Action Plans – List"),
        ("44_action_plan_detail", f"/project-controls/action-plans/{p['action_plan']}/","Project Action Plan – Detail"),
        ("45_logistics_list",     "/project-controls/logistics/",             "Logistics Scenarios – List"),
        ("46_logistics_detail",   f"/project-controls/logistics/{p['logistics']}/","Logistics Scenario – Detail"),
        ("47_logistics_compare",  "/project-controls/logistics/compare/",     "Logistics – Comparison"),
        ("48_transport_units",    "/project-controls/transport-units/",       "Transport Units"),

        # Cost Control
        ("49_cost_dashboard",     "/cost-control/",                           "Cost Control – Dashboard"),
        ("50_cost_codes",         "/cost-control/codes/",                     "Cost Control – Cost Codes"),
        ("51_budget",             "/cost-control/budget/",                    "Cost Control – Budget"),
        ("52_actuals",            "/cost-control/actuals/",                   "Cost Control – Actual Costs"),

        # Safety
        ("53_toolbox_list",       "/safety/toolbox/",                         "Safety – Toolbox Meetings"),
        ("54_safety_inspections", "/safety/inspections/",                     "Safety – Inspections"),
        ("55_safety_insp_detail", f"/safety/inspections/{p['safety_insp']}/", "Safety – Inspection Detail"),
        ("56_incidents",          "/safety/incidents/",                       "Safety – Incidents"),
        ("57_incident_detail",    f"/safety/incidents/{p['incident']}/",      "Safety – Incident Detail"),
        ("58_jsea",               "/safety/jsea/",                            "Safety – JSEA"),

        # Quality
        ("59_quality_dashboard",  "/quality/",                                "Quality – Dashboard"),
        ("60_quality_inspections","/quality/inspections/",                    "Quality – Inspections"),
        ("61_quality_ncr",        "/quality/ncr/",                            "Quality – NCR"),
        ("62_quality_punch",      "/quality/punch-list/",                     "Quality – Punch List"),

        # Documents
        ("63_documents",          "/documents/",                              "Documents – List"),
        ("64_document_detail",    f"/documents/{p['document']}/",             "Document – Detail"),

        # Accounts / Admin
        ("65_profile",            "/accounts/profile/",                       "My Profile"),
        ("66_user_list",          "/accounts/users/",                         "Users – List"),
    ]


# ── Helpers ───────────────────────────────────────────────────────────────────
async def login(page, base: str):
    """Log in to the Django ERP."""
    await page.goto(f"{base}/accounts/login/")
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="username"]', LOGIN_USER)
    await page.fill('input[name="password"]', LOGIN_PASS)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    print("  Logged in OK")


async def screenshot_page(page, base: str, slug: str, path: str, label: str,
                          out_dir: Path) -> dict:
    url = f"{base}{path}"
    dest = out_dir / f"{slug}.png"
    result = {"slug": slug, "label": label, "url": url, "file": str(dest), "status": "ok"}

    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(WAIT_MS / 1000)   # let charts render

        # Check for redirect to login (session expired)
        if "login" in page.url and "login" not in path:
            await login(page, base)
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(WAIT_MS / 1000)

        http_status = response.status if response else 0
        if http_status >= 400:
            result["status"] = f"HTTP {http_status}"
        else:
            await page.screenshot(path=str(dest), full_page=True)

    except Exception as exc:
        result["status"] = f"ERROR: {exc}"

    return result


# ── Main ──────────────────────────────────────────────────────────────────────
async def run(base: str, out_root: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(out_root) / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {out_dir}\n")

    # Determine PKs dynamically
    pks = {
        "project": 2, "daily_report": 36, "equipment": 11,
        "purchase_request": 1, "purchase_order": 1,
        "rock": 73, "sand": 67, "recovery_plan": 1,
        "rap": 2, "action_plan": 1, "logistics": 1,
        "safety_insp": 9, "incident": 5, "document": 2, "payment_claim": 1,
    }

    pages = build_pages(pks)
    results = []
    t0 = time.time()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport=VIEWPORT,
            locale="th-TH",
            timezone_id="Asia/Bangkok",
        )
        page = await context.new_page()

        # Login first
        print("Logging in…")
        await login(page, base)

        # Screenshot each page
        total = len(pages)
        ok = skip = fail = 0
        for i, (slug, path, label) in enumerate(pages, 1):
            print(f"  [{i:02d}/{total}] {label}…", end=" ", flush=True)
            r = await screenshot_page(page, base, slug, path, label, out_dir)
            results.append(r)
            if r["status"] == "ok":
                ok += 1
                print("OK")
            else:
                fail += 1
                print(f"SKIP ({r['status']})")

        await browser.close()

    elapsed = time.time() - t0

    # ── Write index HTML ──────────────────────────────────────────────────────
    index_path = out_dir / "index.html"
    _write_index(index_path, results, ts, elapsed)

    print(f"\n{'─'*60}")
    print(f"Done in {elapsed:.1f}s  |  OK: {ok}  Skipped/Error: {fail}")
    print(f"Index: {index_path}")
    print(f"{'─'*60}\n")


def _write_index(path: Path, results: list, ts: str, elapsed: float):
    rows = ""
    for r in results:
        status_badge = (
            '<span class="badge ok">OK</span>'
            if r["status"] == "ok"
            else f'<span class="badge err">{r["status"]}</span>'
        )
        fname = Path(r["file"]).name
        preview = (
            f'<a href="{fname}" target="_blank"><img src="{fname}" loading="lazy"></a>'
            if r["status"] == "ok"
            else '<span class="no-img">—</span>'
        )
        rows += f"""
        <tr>
          <td>{r['slug']}</td>
          <td>{r['label']}</td>
          <td><a href="{r['url']}" target="_blank">{r['url']}</a></td>
          <td>{status_badge}</td>
          <td class="thumb">{preview}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<title>ERP Page Export – {ts}</title>
<style>
  body {{ font-family: sans-serif; margin: 0; padding: 16px; background: #f4f5f7; }}
  h1 {{ font-size: 1.4rem; color: #1a202c; }}
  p.meta {{ color: #718096; font-size: .85rem; margin: 4px 0 16px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.1); }}
  th {{ background: #2d3748; color: #fff; padding: 10px 12px; text-align: left; font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #e2e8f0; font-size: .82rem; vertical-align: middle; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f7fafc; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: .75rem; font-weight: 600; }}
  .badge.ok  {{ background: #c6f6d5; color: #276749; }}
  .badge.err {{ background: #fed7d7; color: #9b2c2c; }}
  .thumb img {{ width: 180px; height: auto; border: 1px solid #e2e8f0; border-radius: 4px; display: block; }}
  .no-img {{ color: #a0aec0; }}
  a {{ color: #3182ce; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>Construction ERP – Page Export</h1>
<p class="meta">Generated: {ts.replace('_', ' ')} &nbsp;|&nbsp; Total: {len(results)} pages &nbsp;|&nbsp; Elapsed: {elapsed:.1f}s</p>
<table>
  <thead>
    <tr><th>#</th><th>Page</th><th>URL</th><th>Status</th><th>Preview</th></tr>
  </thead>
  <tbody>{rows}
  </tbody>
</table>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export all ERP pages as screenshots")
    parser.add_argument("--base-url", default=DEFAULT_BASE, help="Django dev server URL")
    parser.add_argument("--out",      default=DEFAULT_OUT,  help="Output directory")
    args = parser.parse_args()

    asyncio.run(run(args.base_url, args.out))
