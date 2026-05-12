"""
Responsive viewport tests.
Run: venv\\Scripts\\python.exe tests\\test_responsive.py
"""
import sys
from playwright.sync_api import sync_playwright

VIEWPORTS = [
    ("Desktop 1440", 1440, 900),
    ("Laptop  1280", 1280, 800),
    ("iPad    768",   768, 1024),
    ("iPhone  390",   390,  844),
    ("Android 360",   360,  780),
]
PAGES = [
    ("Dashboard",  "http://127.0.0.1:8000/"),
    ("Projects",   "http://127.0.0.1:8000/projects/"),
    ("DailyRep",   "http://127.0.0.1:8000/daily-reports/"),
]

issues = []

def ok(msg):
    print("  PASS", msg)

def fail(msg):
    print("  FAIL", msg)
    issues.append(msg)


def run():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # Login once, save storage state
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto("http://127.0.0.1:8000/accounts/login/")
        page.fill("[name=username]", "admin")
        page.fill("[name=password]", "Demo@1234")
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")
        storage = ctx.storage_state()
        ctx.close()

        for vp_name, w, h in VIEWPORTS:
            print(f"\n--- {vp_name} ({w}x{h}) ---")
            ctx2 = browser.new_context(
                viewport={"width": w, "height": h},
                storage_state=storage,
            )
            pg = ctx2.new_page()

            for page_name, url in PAGES:
                pg.goto(url, timeout=10000)
                pg.wait_for_load_state("networkidle", timeout=10000)
                label = f"{vp_name}/{page_name}"

                # 1. Sidebar renders
                sidebar = pg.locator("#sidebar")
                if sidebar.count() == 0:
                    fail(f"{label}: #sidebar missing")
                    continue
                ok(f"{label}: #sidebar present")

                # 2. Mobile-specific checks
                if w < 768:
                    # Sidebar off-screen by default
                    box = sidebar.bounding_box()
                    if box and box["x"] >= 0:
                        fail(f"{label}: sidebar visible on mobile load (x={box['x']:.0f})")
                    else:
                        ok(f"{label}: sidebar off-screen on mobile")

                    # Hamburger visible
                    ham = pg.locator("#sidebar-toggler")
                    if ham.count() == 0 or not ham.is_visible():
                        fail(f"{label}: hamburger not visible")
                    else:
                        ok(f"{label}: hamburger visible")

                    # Open sidebar -> backdrop appears
                    ham.click()
                    pg.wait_for_timeout(300)
                    bd = pg.locator("#sidebar-backdrop")
                    bd_box = bd.bounding_box()
                    if bd_box and bd_box["width"] > 0:
                        ok(f"{label}: backdrop shown")
                    else:
                        fail(f"{label}: backdrop NOT shown after hamburger")

                    # Tap backdrop at right edge (outside 260px sidebar) -> sidebar closes
                    bd.click(position={"x": w - 40, "y": h // 2})
                    pg.wait_for_timeout(300)
                    after_box = sidebar.bounding_box()
                    if after_box and after_box["x"] < 0:
                        ok(f"{label}: sidebar closed via backdrop")
                    else:
                        fail(f"{label}: sidebar did not close after backdrop tap")

                # 3. Page content present
                has_content = (
                    pg.locator(".card").count() > 0
                    or pg.locator("table").count() > 0
                    or pg.locator("h4").count() > 0
                )
                if has_content:
                    ok(f"{label}: page content rendered")
                else:
                    fail(f"{label}: no content found")

                # 4. No horizontal body overflow
                overflow = pg.evaluate(
                    "() => document.documentElement.scrollWidth > window.innerWidth + 2"
                )
                if overflow:
                    sw = pg.evaluate("document.documentElement.scrollWidth")
                    fail(f"{label}: horizontal overflow (scrollWidth={sw}, viewport={w})")
                else:
                    ok(f"{label}: no horizontal overflow")

            ctx2.close()

        browser.close()

    print("\n" + "=" * 55)
    if issues:
        print(f"RESULT: {len(issues)} issue(s):")
        for i in issues:
            print(f"  - {i}")
    else:
        print("RESULT: ALL VIEWPORT TESTS PASSED")
    print("=" * 55 + "\n")
    return issues


if __name__ == "__main__":
    result = run()
    sys.exit(1 if result else 0)
