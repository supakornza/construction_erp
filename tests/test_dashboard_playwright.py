"""
Playwright smoke checks for the main Dashboard.

Run while the dev server is active:
    venv\\Scripts\\python.exe tests\\test_dashboard_playwright.py
"""

import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
USER = "admin"
PASS = "Demo@1234"
TIMEOUT = 10_000

failures: list[str] = []


def ok(message: str) -> None:
    print(f"  PASS  {message}")


def fail(message: str) -> None:
    print(f"  FAIL  {message}")
    failures.append(message)


def section(title: str) -> None:
    print(f"\n{'-' * 60}\n  {title}\n{'-' * 60}")


def do_login(page) -> bool:
    page.goto(f"{BASE}/accounts/login/", timeout=TIMEOUT)
    page.locator("input[name='username']").fill(USER)
    page.locator("input[name='password']").fill(PASS)
    page.locator("button[type='submit']").click()
    page.wait_for_load_state("networkidle", timeout=TIMEOUT)
    if "/accounts/login/" in page.url:
        fail(f"Login failed, still on {page.url}")
        return False
    ok(f"Logged in as {USER!r}")
    return True


def expect_count(page, selector: str, minimum: int, label: str) -> None:
    count = page.locator(selector).count()
    if count < minimum:
        fail(f"{label}: expected at least {minimum}, found {count}")
    else:
        ok(f"{label}: found {count}")


def run():
    console_errors: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(f"PageError: {exc}"))

        section("Authentication")
        if not do_login(page):
            browser.close()
            return failures

        section("Dashboard Layout")
        page.goto(f"{BASE}/", timeout=TIMEOUT)
        page.wait_for_load_state("networkidle", timeout=15_000)
        expect_count(page, ".bs-kpi", 4, "KPI cards")
        expect_count(page, ".bs-card", 7, "dashboard cards")
        expect_count(page, ".bs-quick-link", 8, "quick access links")
        expect_count(page, "#cashFlowChart", 1, "cash flow chart")
        expect_count(page, "#budgetActualChart", 1, "budget chart")

        section("Project Filter")
        project_filter = page.locator("select[name='project']")
        if project_filter.count() != 1:
            fail("Project filter select not found")
        else:
            first_value = project_filter.evaluate(
                "el => Array.from(el.options).map(o => o.value).find(Boolean) || ''"
            )
            if first_value:
                page.goto(f"{BASE}/?project={first_value}", timeout=TIMEOUT)
                page.wait_for_load_state("networkidle", timeout=TIMEOUT)
                selected_value = page.locator("select[name='project']").evaluate("el => el.value")
                if selected_value == first_value:
                    ok("Project filter preserves the selected dashboard scope")
                else:
                    fail(f"Project filter did not preserve selection, got {selected_value!r}")
            else:
                ok("Project filter present; no project options available to select")

        visible_text = page.locator(".bs-dashboard").inner_text(timeout=TIMEOUT)
        for text in ["Project Status Overview", "Project Progress", "Quick Access"]:
            if text in visible_text:
                ok(f"Visible section: {text}")
            else:
                fail(f"Missing visible section: {text}")

        meaningful_errors = [e for e in console_errors if "favicon" not in e.lower()]
        if meaningful_errors:
            section("JavaScript Console Errors")
            for error in meaningful_errors:
                fail(error)

        browser.close()

    print("\n" + "=" * 60)
    if failures:
        print(f"  RESULT: {len(failures)} FAILURE(S)")
        for index, item in enumerate(failures, 1):
            print(f"  {index}. {item}")
    else:
        print("  RESULT: ALL CHECKS PASSED")
    print("=" * 60 + "\n")
    return failures


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
