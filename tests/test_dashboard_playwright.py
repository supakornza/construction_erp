"""
Playwright tests for the Executive Dashboard.

Covers:
  - Page load: KPI cards, chart canvases rendered
  - #project-selector  → triggers /chart-data/ AND /scurve/ with project_id
  - #scurve-project    → triggers /scurve/ with project_id
  - Range radios 7 / 30 days → auto-fetch /chart-data/ with correct range param
  - Range radio Custom → enables #date-from / #date-to inputs
  - Apply button with custom dates → /chart-data/ with range=custom + date params
  - .chart-range-label text updates after each fetch

Run:
    venv\\Scripts\\python.exe tests\\test_dashboard_playwright.py
"""

import re
import sys
from playwright.sync_api import sync_playwright

BASE    = "http://127.0.0.1:8000"
USER    = "admin"
PASS    = "Demo@1234"
TIMEOUT = 10_000   # ms per interaction

CHART_API  = re.compile(r"/chart-data/")
SCURVE_API = re.compile(r"/scurve/")

# ── Helpers ───────────────────────────────────────────────────────────────────

PASS_ICON = "PASS"
FAIL_ICON = "FAIL"

failures: list[str] = []

def ok(msg: str) -> None:
    print(f"  {PASS_ICON}  {msg}")

def fail(msg: str) -> None:
    print(f"  {FAIL_ICON}  {msg}")
    failures.append(msg)

def section(title: str) -> None:
    print(f"\n{'-'*60}\n  {title}\n{'-'*60}")

# ── Login helper ──────────────────────────────────────────────────────────────

def do_login(page) -> bool:
    page.goto(f"{BASE}/accounts/login/", timeout=TIMEOUT)
    page.locator("input[name='username']").fill(USER)
    page.locator("input[name='password']").fill(PASS)
    with page.expect_response(lambda r: r.status < 400, timeout=TIMEOUT):
        page.locator("button[type='submit']").click()

    page.wait_for_load_state("networkidle", timeout=TIMEOUT)
    if "/accounts/login/" in page.url:
        fail(f"Login failed – still on {page.url}")
        return False
    ok(f"Logged in as {USER!r}")
    return True

# ── Individual checks ─────────────────────────────────────────────────────────

def check_kpi_cards(page) -> None:
    section("KPI cards visible")
    cards = page.locator(".kpi-card, .exec-kpi-card")
    n = cards.count()
    if n == 0:
        fail("No .kpi-card / .exec-kpi-card elements found")
    else:
        ok(f"{n} KPI card(s) rendered")


def check_charts_exist(page) -> None:
    section("Chart canvas elements")
    for cid in ("manpowerChart", "rockChart", "sandChart"):
        el = page.locator(f"#{cid}")
        if el.count() == 0:
            fail(f"#{cid} canvas not found in DOM")
        else:
            ok(f"#{cid} canvas present")


def check_project_selector(page) -> None:
    section("Project selector (#project-selector)")

    sel = page.locator("#project-selector")
    if sel.count() == 0:
        fail("#project-selector not found")
        return

    opts = sel.locator("option")
    if opts.count() <= 1:
        fail("No project options (only 'All Projects'); skipping filter test")
        return

    # Pick the first real project (index 1 = first after "All Projects")
    first_val = opts.nth(1).get_attribute("value")
    ok(f"Selecting project id={first_val!r}")

    # Both /chart-data/ and /scurve/ must fire
    chart_req  = []
    scurve_req = []

    def on_request(req):
        if CHART_API.search(req.url):
            chart_req.append(req.url)
        if SCURVE_API.search(req.url):
            scurve_req.append(req.url)

    page.on("request", on_request)
    sel.select_option(value=str(first_val))
    page.wait_for_timeout(2000)   # allow both fetches to fire
    page.remove_listener("request", on_request)

    if not chart_req:
        fail("project change: /chart-data/ request not fired")
    elif f"project_id={first_val}" not in chart_req[0]:
        fail(f"project change: /chart-data/ missing project_id — got {chart_req[0]}")
    else:
        ok(f"/chart-data/ called with project_id: {chart_req[0]}")

    if not scurve_req:
        fail("project change: /scurve/ request not fired")
    elif f"project_id={first_val}" not in scurve_req[0]:
        fail(f"project change: /scurve/ missing project_id — got {scurve_req[0]}")
    else:
        ok(f"/scurve/ called with project_id: {scurve_req[0]}")

    # Reset to "All Projects"
    sel.select_option(value="")
    page.wait_for_timeout(500)


def check_scurve_selector(page) -> None:
    section("S-Curve project selector (#scurve-project)")

    sel = page.locator("#scurve-project")
    if sel.count() == 0:
        fail("#scurve-project not found")
        return

    opts = sel.locator("option")
    n_opts = opts.count()
    if n_opts == 0:
        fail("#scurve-project has no options")
        return

    ok(f"#scurve-project found with {n_opts} option(s)")

    if n_opts < 2:
        ok("Only 1 project in DB — cannot trigger change event; skipping request check")
        return

    # Select a different option to trigger the change event
    seen: list[str] = []
    def _listener(r):
        if SCURVE_API.search(r.url):
            seen.append(r.url)

    page.on("request", _listener)
    sel.select_option(index=1)
    page.wait_for_timeout(1500)
    page.remove_listener("request", _listener)

    if not seen:
        fail("S-curve selector change: /scurve/ not requested")
    else:
        ok(f"/scurve/ called: {seen[-1]}")


def check_range_7(page) -> None:
    section("Range radio – 7 Days (#range-7)")

    seen: list[str] = []
    def _listener(r):
        if CHART_API.search(r.url):
            seen.append(r.url)

    page.on("request", _listener)
    page.locator("label[for='range-7']").click()
    page.wait_for_timeout(2000)
    page.remove_listener("request", _listener)

    chart_calls = [u for u in seen if CHART_API.search(u)]
    if not chart_calls:
        fail("range-7: /chart-data/ not requested after clicking 7-day radio")
        return

    url = chart_calls[-1]
    if "range=7" not in url:
        fail(f"range-7: expected range=7 in URL, got {url}")
    else:
        ok(f"range=7 in URL: {url}")

    # Range label should update
    lbl = page.locator(".chart-range-label").first.text_content(timeout=3000)
    if "7" in lbl:
        ok(f".chart-range-label updated: {lbl!r}")
    else:
        fail(f".chart-range-label did not update to 7 days: {lbl!r}")


def check_range_30(page) -> None:
    section("Range radio – 30 Days (#range-30)")

    seen: list[str] = []
    def _listener(r):
        if CHART_API.search(r.url):
            seen.append(r.url)

    page.on("request", _listener)
    page.locator("label[for='range-30']").click()
    page.wait_for_timeout(2000)
    page.remove_listener("request", _listener)

    chart_calls = [u for u in seen if CHART_API.search(u)]
    if not chart_calls:
        fail("range-30: /chart-data/ not requested after clicking 30-day radio")
        return

    url = chart_calls[-1]
    if "range=30" not in url:
        fail(f"range-30: expected range=30 in URL, got {url}")
    else:
        ok(f"range=30 in URL: {url}")


def check_custom_range(page) -> None:
    section("Range radio – Custom + Apply (#range-custom, #apply-chart-filter)")

    # Click Custom radio
    page.locator("label[for='range-custom']").click()
    page.wait_for_timeout(300)

    # Date inputs must be enabled
    date_from = page.locator("#date-from")
    date_to   = page.locator("#date-to")

    if date_from.is_disabled():
        fail("#date-from still disabled after selecting Custom range")
    else:
        ok("#date-from enabled")

    if date_to.is_disabled():
        fail("#date-to still disabled after selecting Custom range")
    else:
        ok("#date-to enabled")

    # Fill dates
    date_from.fill("2025-01-01")
    date_to.fill("2025-03-31")

    # Click Apply and capture the chart-data request
    seen: list[str] = []
    def _listener(r):
        if CHART_API.search(r.url):
            seen.append(r.url)

    page.on("request", _listener)
    page.locator("#apply-chart-filter").click()
    page.wait_for_timeout(2000)
    page.remove_listener("request", _listener)

    chart_calls = [u for u in seen if CHART_API.search(u)]
    if not chart_calls:
        fail("Apply: /chart-data/ not requested")
        return

    url = chart_calls[-1]
    ok(f"Apply triggered: {url}")

    if "range=custom" not in url:
        fail(f"Apply: expected range=custom, got {url}")
    else:
        ok("range=custom present")

    if "date_from=2025-01-01" not in url:
        fail(f"Apply: date_from missing in URL: {url}")
    else:
        ok("date_from=2025-01-01 present")

    if "date_to=2025-03-31" not in url:
        fail(f"Apply: date_to missing in URL: {url}")
    else:
        ok("date_to=2025-03-31 present")

    # Range label should show the custom date range
    page.wait_for_timeout(500)
    lbl = page.locator(".chart-range-label").first.text_content(timeout=3000)
    if "2025-01-01" in lbl or "2025" in lbl:
        ok(f".chart-range-label shows custom range: {lbl!r}")
    else:
        fail(f".chart-range-label did not show custom dates: {lbl!r}")


def check_console_errors(page) -> list[str]:
    """Return any JS console errors that occurred on the page."""
    return []   # errors are collected via on('console') — set up before navigation


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    console_errors: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx  = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # Collect JS console errors throughout the session
        page.on("console", lambda msg: console_errors.append(msg.text)
                if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(f"PageError: {exc}"))

        print("\n" + "="*60)
        print("  Dashboard Filter Tests")
        print("="*60)

        # Login
        section("Authentication")
        if not do_login(page):
            browser.close()
            return

        # Navigate to dashboard and wait for charts to load
        page.goto(f"{BASE}/", timeout=TIMEOUT)
        page.wait_for_load_state("networkidle", timeout=15_000)

        # Run all checks
        check_kpi_cards(page)
        check_charts_exist(page)
        check_project_selector(page)
        check_scurve_selector(page)
        check_range_7(page)
        check_range_30(page)
        check_custom_range(page)

        # JS errors
        if console_errors:
            section("JavaScript Console Errors")
            for err in console_errors:
                # Ignore favicon 404s and unrelated noise
                if "favicon" in err.lower():
                    continue
                fail(f"JS error: {err}")

        browser.close()

    # ── Summary ───────────────────────────────────────────────
    print("\n" + "="*60)
    if failures:
        print(f"  RESULT: {len(failures)} FAILURE(S)")
        for i, f in enumerate(failures, 1):
            print(f"  {i}. {f}")
    else:
        print("  RESULT: ALL CHECKS PASSED")
    print("="*60 + "\n")
    return failures


if __name__ == "__main__":
    result = run()
    sys.exit(1 if result else 0)
