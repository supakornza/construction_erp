"""
Patch: create RockDashboardSettings and SandDashboardSettings for CON-2025-002
so that Completion / Remaining Qty / Forecast Completion show real values.
"""
import sys, os
from datetime import date
from decimal import Decimal

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import django; django.setup()

from apps.projects.models import Project
from apps.project_controls.models import RockDashboardSettings, SandDashboardSettings

CONTRACT_NO = "CON-2025-002"
proj = Project.objects.filter(contract_no=CONTRACT_NO).first()
if not proj:
    print("Project not found.")
    sys.exit(1)

# ── Rock ─────────────────────────────────────────────────────
# BOQ 3.1: Core Rock 60,000 Ton  |  BOQ 3.2: Armour Rock 12,000 Ton
# Rock dashboard tracks Core Rock placement → target = 60,000 T
rock_settings, created = RockDashboardSettings.objects.get_or_create(
    project=proj,
    defaults=dict(
        target_quantity_ton=Decimal("60000"),
        daily_target_placement_ton=Decimal("400"),  # 60,000 T / 150 working days
        planned_start_date=date(2025, 11, 1),
        planned_finish_date=date(2026, 4, 30),
    )
)
if not created:
    # Update if already exists but has no target
    if rock_settings.target_quantity_ton is None:
        rock_settings.target_quantity_ton = Decimal("60000")
        rock_settings.daily_target_placement_ton = Decimal("400")
        rock_settings.planned_start_date = date(2025, 11, 1)
        rock_settings.planned_finish_date = date(2026, 4, 30)
        rock_settings.save()
        print(f"Rock settings UPDATED for {proj}")
    else:
        print(f"Rock settings already set (target={rock_settings.target_quantity_ton} T)")
else:
    print(f"Rock settings CREATED for {proj} — target 60,000 T @ 400 T/day")

# ── Sand ─────────────────────────────────────────────────────
# BOQ 5.1: Marine Dredging 25,000 m3  → use as sand target
sand_settings, created = SandDashboardSettings.objects.get_or_create(
    project=proj,
    defaults=dict(
        target_quantity_ton=Decimal("25000"),
        daily_target_delivery_ton=Decimal("200"),
        daily_target_placement_ton=Decimal("180"),
        planned_start_date=date(2026, 1, 1),
        planned_finish_date=date(2026, 6, 30),
    )
)
if not created:
    if sand_settings.target_quantity_ton is None:
        sand_settings.target_quantity_ton = Decimal("25000")
        sand_settings.daily_target_delivery_ton = Decimal("200")
        sand_settings.daily_target_placement_ton = Decimal("180")
        sand_settings.save()
        print(f"Sand settings UPDATED for {proj}")
    else:
        print(f"Sand settings already set (target={sand_settings.target_quantity_ton} T)")
else:
    print(f"Sand settings CREATED for {proj} — target 25,000 T @ 180 T/day placed")

print("Done.")
