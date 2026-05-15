"""
Test Scenario Seed Script
Creates a complete project: "Sattahip Port Breakwater Phase 2"
with realistic data across all modules.

Usage:
    python scripts/seed_test_scenario.py
    python scripts/seed_test_scenario.py --delete   # delete scenario first
"""
import sys, os, random, argparse
from datetime import date, timedelta
from decimal import Decimal

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import django; django.setup()

from django.db import transaction
from apps.projects.models import Project
from apps.boq.models import BOQItem, DailyProgressRecord
from apps.daily_reports.models import DailyReport
from apps.manpower.models import DailyManpowerRecord, ManpowerCategory
from apps.equipment.models import Equipment, DailyEquipmentRecord
from apps.materials.models import Material, MaterialDelivery, MaterialCategory
from apps.procurement.models import Supplier, PurchaseRequest, PurchaseOrder, PurchaseRequestItem as PRItem, PurchaseOrderItem as POItem
from apps.project_controls.models import (
    RockDailyRecord, RockBargePlacement,
    SandDailyRecord, SandBargePlacement,
    RevetmentStation, RevetmentActivity, RevetmentDailyRecord, RevetmentDailyItem,
)
from apps.safety.models import SafetyInspection, IncidentReport, ToolboxMeeting
from apps.quality.models import InspectionRequest as QualityInspection, NonConformance as NonConformanceReport
from apps.cost_control.models import CostCode, BudgetItem, ActualCost
from apps.accounts.models import User

rng = random.Random(42)

# ─────────────────────────────────────────────────────────
CONTRACT_NO   = "CON-2025-002"
PROJECT_NAME  = "Sattahip Port Breakwater Phase 2"
LOCATION      = "Sattahip, Chonburi, Thailand"
CONTRACT_VAL  = Decimal("95000000")
START_DATE    = date(2025, 11, 1)
END_DATE      = date(2026, 7, 31)
TODAY         = date.today()          # 2026-05-15
# ─────────────────────────────────────────────────────────

def log(msg): print(f"  {msg}")

def delete_scenario():
    proj = Project.objects.filter(contract_no=CONTRACT_NO).first()
    if not proj:
        print("Scenario not found – nothing to delete."); return
    print(f"Deleting scenario project {CONTRACT_NO}…")
    proj.delete()
    Supplier.objects.filter(name__startswith="[TEST]").delete()
    print("Done.")


@transaction.atomic
def run():
    print(f"\n{'='*60}")
    print(f"  Creating test scenario: {PROJECT_NAME}")
    print(f"{'='*60}\n")

    # ── Users (use existing) ──────────────────────────────
    admin   = User.objects.filter(is_superuser=True).first()
    pm      = User.objects.filter(username="eng_sara").first() or admin
    eng     = User.objects.filter(username="arnon_k").first()  or admin
    safety  = User.objects.filter(username="chaiwat_p").first() or admin

    # ── Equipment (use existing active barges + plant) ────
    barges      = list(Equipment.objects.filter(category__name="Barge", status="Active"))
    excavators  = list(Equipment.objects.filter(category__name="Excavator", status="Active"))
    trucks      = list(Equipment.objects.filter(category__name="Truck", status="Active"))
    loaders     = list(Equipment.objects.filter(category__name="Loader", status="Active"))
    cranes      = list(Equipment.objects.filter(category__name="Crane", status="Active"))
    all_equip   = barges + excavators + trucks + loaders + cranes

    # ── Materials (use existing) ──────────────────────────
    core_rock   = Material.objects.filter(name__icontains="Core Rock").first()
    armour_rock = Material.objects.filter(name__icontains="Armour Rock").first()
    sand_mat    = Material.objects.filter(name__icontains="Sand").first()
    geotextile  = Material.objects.filter(name__icontains="Geotextile").first()

    # ── Suppliers ─────────────────────────────────────────
    print("1. Creating suppliers…")
    sup_rock, _ = Supplier.objects.get_or_create(
        name="[TEST] Sattahip Quarry Co., Ltd.",
        defaults=dict(contact_person="Somchai T.", phone="038-000001",
                      email="info@sattahip-quarry.test", address="Sattahip, Chonburi")
    )
    sup_marine, _ = Supplier.objects.get_or_create(
        name="[TEST] Marine Works Co., Ltd.",
        defaults=dict(contact_person="Napat W.", phone="02-000002",
                      email="bid@marineworks.test", address="Bangkok")
    )
    sup_geo, _ = Supplier.objects.get_or_create(
        name="[TEST] Geosynthetics Asia Co., Ltd.",
        defaults=dict(contact_person="Priya K.", phone="02-000003",
                      email="sales@geosyn.test", address="Bangkok")
    )
    log(f"Suppliers: {sup_rock.name}, {sup_marine.name}, {sup_geo.name}")

    # ── Project ───────────────────────────────────────────
    print("2. Creating project…")
    proj, created = Project.objects.get_or_create(
        contract_no=CONTRACT_NO,
        defaults=dict(
            project_name=PROJECT_NAME,
            location=LOCATION,
            owner="Port Authority of Thailand",
            contractor="Marine Construction Co., Ltd.",
            consultant="Coastal Engineering Consultants Co., Ltd.",
            contract_value=CONTRACT_VAL,
            start_date=START_DATE,
            finish_date=END_DATE,
            status="Active",
            description=(
                "Construction of breakwater extension (Phase 2) at Sattahip Port, "
                "including core rock placement, armour layer, geotextile filter, "
                "and revetment works. Total breakwater length: 450m."
            ),
        )
    )
    if not created:
        print(f"  Project {CONTRACT_NO} already exists – updating…")
    log(f"Project: {proj.project_name} [{proj.pk}]")

    # ── BOQ Items ─────────────────────────────────────────
    print("3. Creating BOQ items…")
    boq_defs = [
        ("1.1", "Mobilization & Demobilization",          "LS",   1,       2_000_000),
        ("2.1", "Temporary Works & Cofferdam",             "LS",   1,       3_500_000),
        ("3.1", "Core Rock Supply & Placement",            "Ton",  60_000,  750),
        ("3.2", "Armour Rock (1-3T) Supply & Placement",  "Ton",  12_000,  1_400),
        ("4.1", "Geotextile Filter Layer Installation",   "m²",   18_000,  95),
        ("4.2", "Revetment Works (Concrete Armour Block)","m²",   4_500,   1_800),
        ("5.1", "Marine Dredging",                        "m³",   25_000,  280),
        ("6.1", "Yard Improvement & Drainage",            "m²",   3_000,   650),
    ]
    boq_items = {}
    for item_no, desc, unit, qty, rate in boq_defs:
        boq, _ = BOQItem.objects.get_or_create(
            project=proj, item_no=item_no,
            defaults=dict(description=desc, unit=unit,
                          contract_quantity=qty, unit_rate=rate)
        )
        boq_items[item_no] = boq
        log(f"  BOQ {item_no}: {desc} ({qty:,} {unit} × ฿{rate:,})")

    # ── Build daily date range (working days only, skip Sunday) ──
    work_dates = []
    d = START_DATE
    while d <= TODAY:
        if d.weekday() != 6:   # skip Sunday
            work_dates.append(d)
        d += timedelta(days=1)
    log(f"Working days to simulate: {len(work_dates)}")

    # ── Daily Reports ─────────────────────────────────────
    print("4. Creating daily reports…")
    weather_choices = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Heavy Rain"]

    reports_by_date = {}
    created_count = 0
    for i, d in enumerate(work_dates):
        # Alternate between Approved (older) and Draft (recent 14 days)
        if (TODAY - d).days <= 14:
            status = "Draft"
        elif (TODAY - d).days <= 30:
            status = rng.choice(["Draft", "Approved"])
        else:
            status = "Approved"

        weather = rng.choice(weather_choices)
        rain_day = "Rain" in weather

        rpt, created = DailyReport.objects.get_or_create(
            project=proj,
            report_date=d,
            defaults=dict(
                prepared_by=pm,
                status=status,
                weather_morning=weather,
                weather_afternoon="Sunny" if not rain_day else "Rainy",
                remarks=f"Day {i+1} - {weather}. Works progressing as planned." if not rain_day
                        else "Rain delay. Works suspended for morning session.",
            )
        )
        reports_by_date[d] = rpt
        if created: created_count += 1
    log(f"Daily reports created: {created_count} / {len(work_dates)}")

    # ── Manpower Records ──────────────────────────────────
    print("5. Creating manpower records…")
    mp_cats = list(ManpowerCategory.objects.all())
    mp_profiles = {
        "Engineer":      (3, 5),
        "Foreman":       (4, 7),
        "Operator":      (8, 14),
        "GeneralWorker": (25, 45),
        "Driver":        (4, 8),
        "SafetyOfficer": (2, 3),
        "Surveyor":      (1, 2),
    }
    mp_count = 0
    for d in work_dates:
        rpt = reports_by_date.get(d)
        if not rpt: continue
        rain_day = "Rain" in (rpt.weather_morning or "")
        factor = 0.4 if rain_day else 1.0
        for cat in mp_cats:
            lo, hi = mp_profiles.get(cat.name, (2, 5))
            qty = int(rng.randint(lo, hi) * factor)
            if qty == 0: continue
            _, c = DailyManpowerRecord.objects.get_or_create(
                project=proj, report_date=d, category=cat,
                defaults=dict(quantity=qty)
            )
            if c: mp_count += 1
    log(f"Manpower records created: {mp_count}")

    # ── Equipment Records ─────────────────────────────────
    print("6. Creating equipment records…")
    eq_count = 0
    daily_equip_pool = (barges[:3] + excavators[:2] + trucks[:2]
                        + loaders[:1] + cranes[:1])[:8]
    for d in work_dates:
        rain_day = "Rain" in (reports_by_date.get(d, DailyReport()).weather_morning or "")
        for eq in daily_equip_pool:
            if rain_day and eq in barges and rng.random() < 0.6:
                status = "Standby"
            elif rng.random() < 0.08:
                status = "Breakdown"
            elif rng.random() < 0.1:
                status = "Standby"
            else:
                status = "Working"
            hours = rng.uniform(6, 10) if status == "Working" else 0
            _, c = DailyEquipmentRecord.objects.get_or_create(
                project=proj, report_date=d, equipment=eq,
                defaults=dict(status=status, working_hours=round(hours, 1))
            )
            if c: eq_count += 1
    log(f"Equipment records created: {eq_count}")

    # ── Material Deliveries ───────────────────────────────
    print("7. Creating material deliveries…")
    del_count = 0
    # Rock delivered ~4-5 times per week, sand ~2-3 times per week
    for d in work_dates:
        rain_day = "Rain" in (reports_by_date.get(d, DailyReport()).weather_morning or "")
        if rain_day and rng.random() < 0.5:
            continue

        # Core Rock deliveries
        if core_rock and rng.random() < 0.75:
            for _ in range(rng.randint(1, 3)):
                qty = round(rng.uniform(180, 420), 1)
                _, c = MaterialDelivery.objects.get_or_create(
                    project=proj, material=core_rock, delivery_date=d,
                    source=sup_rock.name,
                    defaults=dict(quantity=qty, unit_price=750,
                                  delivery_note_no=f"DN-CR-{d.strftime('%Y%m%d')}-{_+1}")
                )
                if c: del_count += 1

        # Armour Rock deliveries (less frequent)
        if armour_rock and rng.random() < 0.35:
            qty = round(rng.uniform(80, 200), 1)
            _, c = MaterialDelivery.objects.get_or_create(
                project=proj, material=armour_rock, delivery_date=d,
                source=sup_rock.name,
                defaults=dict(quantity=qty, unit_price=1400,
                              delivery_note_no=f"DN-AR-{d.strftime('%Y%m%d')}")
            )
            if c: del_count += 1

        # Sand deliveries
        if sand_mat and rng.random() < 0.45:
            qty = round(rng.uniform(120, 350), 1)
            _, c = MaterialDelivery.objects.get_or_create(
                project=proj, material=sand_mat, delivery_date=d,
                source=sup_marine.name,
                defaults=dict(quantity=qty, unit_price=280,
                              delivery_note_no=f"DN-SD-{d.strftime('%Y%m%d')}")
            )
            if c: del_count += 1

        # Geotextile (only mid-phase, ~days 90-160)
        if geotextile and 90 <= (d - START_DATE).days <= 160:
            if rng.random() < 0.25:
                qty = round(rng.uniform(500, 1500), 1)
                _, c = MaterialDelivery.objects.get_or_create(
                    project=proj, material=geotextile, delivery_date=d,
                    source=sup_geo.name,
                    defaults=dict(quantity=qty, unit_price=95,
                                  delivery_note_no=f"DN-GT-{d.strftime('%Y%m%d')}")
                )
                if c: del_count += 1
    log(f"Material deliveries created: {del_count}")

    # ── Rock Daily Records & Placements ──────────────────
    print("8. Creating Rock daily records…")
    rock_barge = barges[0] if barges else None
    rock_count = 0
    rock_accum = 0.0
    for d in work_dates:
        rain_day = "Rain" in (reports_by_date.get(d, DailyReport()).weather_morning or "")
        if rain_day and rng.random() < 0.6: continue
        daily_ton = round(rng.uniform(250, 680), 1)
        rock_accum += daily_ton
        trips = rng.randint(8, 20)
        rr, c = RockDailyRecord.objects.get_or_create(
            project=proj, record_date=d,
            defaults=dict(
                material_type="Core Rock",
                source_quarry=sup_rock.name,
                destination_area="Breakwater BW-Ph2 Sta.0+000-0+450",
                tct_daily_ton=daily_ton,
                tct_accum_ton=round(rock_accum, 1),
                tct_trips=trips,
                tct_trucks=rng.randint(4, 10),
                placed_daily_ton=round(daily_ton * rng.uniform(0.85, 0.99), 1),
                placed_accum_ton=round(rock_accum * 0.93, 1),
                station_of_core="Sta.0+000-0+450",
                remarks="" if not rain_day else "Morning rain delay",
                created_by=eng,
            )
        )
        if c:
            rock_count += 1
            if rock_barge:
                RockBargePlacement.objects.get_or_create(
                    record=rr, barge=rock_barge,
                    defaults=dict(quantity_ton=daily_ton, trips=trips)
                )
    log(f"Rock daily records created: {rock_count} (accum {rock_accum:,.0f} T)")

    # ── Sand Daily Records & Placements ──────────────────
    print("9. Creating Sand daily records…")
    sand_barge = barges[1] if len(barges) > 1 else rock_barge
    sand_count = 0
    sand_accum = 0.0
    # Sand works started ~day 60 onwards
    sand_start = START_DATE + timedelta(days=60)
    for d in work_dates:
        if d < sand_start: continue
        rain_day = "Rain" in (reports_by_date.get(d, DailyReport()).weather_morning or "")
        if rain_day and rng.random() < 0.7: continue
        daily_m3 = round(rng.uniform(80, 320), 1)
        sand_accum += daily_m3
        sr, c = SandDailyRecord.objects.get_or_create(
            project=proj, record_date=d,
            defaults=dict(
                day_name=d.strftime("%A"),
                tct_daily_ton=Decimal(str(round(daily_m3 * 0.6, 1))),
                tct_accum_ton=Decimal(str(round(sand_accum * 0.6, 1))),
                total_daily_ton=Decimal(str(daily_m3)),
                total_accum_ton=Decimal(str(round(sand_accum, 1))),
                offshore_daily_ton=Decimal(str(round(daily_m3 * 0.7, 1))),
                offshore_accum_ton=Decimal(str(round(sand_accum * 0.7, 1))),
                sand_source="Sattahip Bay",
                remarks="" if not rain_day else "Rain delay",
                created_by=eng,
            )
        )
        if c:
            sand_count += 1
            if sand_barge:
                SandBargePlacement.objects.get_or_create(
                    record=sr, barge=sand_barge,
                    defaults=dict(quantity_ton=Decimal(str(daily_m3)), trips=rng.randint(2, 6),
                                  destination="Reclamation Area A - Sattahip Ph2")
                )
    log(f"Sand daily records created: {sand_count} (accum {sand_accum:,.0f} m³)")

    # ── Revetment Records ─────────────────────────────────
    print("10. Creating revetment records…")
    rev_start = START_DATE + timedelta(days=100)
    rev_count = 0
    # Create station and activity definitions first
    stn, _ = RevetmentStation.objects.get_or_create(
        project=proj, station="0+000~0+450",
        defaults=dict(sop="BW-Ph2", sort_order=1)
    )
    act, _ = RevetmentActivity.objects.get_or_create(
        project=proj, name="Concrete Armour Block Placement", template_column="A1",
        defaults=dict(group_name="Armour Layer", unit="m²", sort_order=1)
    )
    for d in work_dates:
        if d < rev_start: continue
        if rng.random() < 0.55: continue
        qty = round(rng.uniform(60, 200), 1)
        rec, c = RevetmentDailyRecord.objects.get_or_create(
            project=proj, record_date=d,
            defaults=dict(
                day_name=d.strftime("%A"),
                remarks="Concrete armour block placement — Breakwater BW-Ph2",
                created_by=eng,
            )
        )
        if c:
            RevetmentDailyItem.objects.get_or_create(
                record=rec, station=stn, activity=act,
                defaults=dict(quantity_done=Decimal(str(qty)), status="Ongoing")
            )
            rev_count += 1
    log(f"Revetment records created: {rev_count}")

    # ── BOQ Progress Records ──────────────────────────────
    print("11. Creating BOQ progress records…")
    prog_count = 0
    # Map materials to BOQ items
    boq_progress_plan = {
        "3.1": ("Ton",  core_rock,   0.90),   # 90% target completion
        "3.2": ("Ton",  armour_rock, 0.45),
        "4.1": ("m²",   geotextile,  0.60),
        "5.1": ("m³",   None,        0.70),
        "1.1": ("LS",   None,        1.00),
        "2.1": ("LS",   None,        0.85),
    }
    for item_no, (unit, mat, target_pct) in boq_progress_plan.items():
        boq = boq_items.get(item_no)
        if not boq: continue
        target_qty = float(boq.contract_quantity) * target_pct
        applicable_days = [d for d in work_dates
                           if (d - START_DATE).days >= (30 if item_no not in ("1.1","2.1") else 0)]
        if not applicable_days: continue
        daily_qty = target_qty / len(applicable_days)
        for d in applicable_days:
            noise = rng.uniform(0.5, 1.5)
            qty = round(daily_qty * noise, 2)
            if qty <= 0: continue
            _, c = DailyProgressRecord.objects.get_or_create(
                project=proj, boq_item=boq, record_date=d,
                defaults=dict(daily_quantity=qty)
            )
            if c: prog_count += 1
    log(f"BOQ progress records created: {prog_count}")

    # ── Procurement ───────────────────────────────────────
    print("12. Creating procurement records…")
    pr1, _ = PurchaseRequest.objects.get_or_create(
        pr_no="PR-2025-0001",
        defaults=dict(
            project=proj, requested_by=pm, status="Approved",
            request_date=START_DATE,
            required_date=START_DATE + timedelta(days=14),
            remarks="Core rock supply for breakwater Phase 2 commencement",
        )
    )
    if core_rock:
        PRItem.objects.get_or_create(
            pr=pr1, material=core_rock,
            defaults=dict(quantity=30000, unit="Ton", estimated_price=Decimal("22500000"))
        )
    pr2, _ = PurchaseRequest.objects.get_or_create(
        pr_no="PR-2025-0002",
        defaults=dict(
            project=proj, requested_by=eng, status="Approved",
            request_date=START_DATE + timedelta(days=85),
            required_date=START_DATE + timedelta(days=90),
        )
    )
    if geotextile:
        PRItem.objects.get_or_create(
            pr=pr2, material=geotextile,
            defaults=dict(quantity=18000, unit="m2", estimated_price=Decimal("1710000"))
        )
    pr3, _ = PurchaseRequest.objects.get_or_create(
        pr_no="PR-2026-0001",
        defaults=dict(
            project=proj, requested_by=pm, status="Submitted",
            request_date=TODAY - timedelta(days=5),
            required_date=TODAY + timedelta(days=21),
        )
    )
    if armour_rock:
        PRItem.objects.get_or_create(
            pr=pr3, material=armour_rock,
            defaults=dict(quantity=6000, unit="Ton", estimated_price=Decimal("8400000"))
        )
    log("PRs created: PR-2025-0001, PR-2025-0002, PR-2026-0001")

    po1, _ = PurchaseOrder.objects.get_or_create(
        po_no="PO-2025-0001",
        defaults=dict(
            pr=pr1, supplier=sup_rock,
            status="PartialDelivered",
            order_date=START_DATE + timedelta(days=5),
            delivery_date=START_DATE + timedelta(days=90),
            total_amount=Decimal("21600000"),
        )
    )
    if core_rock and not po1.items.exists():
        POItem.objects.create(
            po=po1, material=core_rock,
            quantity=30000, unit_price=Decimal("720"),
            total_price=Decimal("21600000"), delivered_quantity=27000,
        )
    po2, _ = PurchaseOrder.objects.get_or_create(
        po_no="PO-2025-0002",
        defaults=dict(
            pr=pr2, supplier=sup_geo,
            status="Delivered",
            order_date=START_DATE + timedelta(days=80),
            delivery_date=START_DATE + timedelta(days=100),
            total_amount=Decimal("1620000"),
        )
    )
    if geotextile and not po2.items.exists():
        POItem.objects.create(
            po=po2, material=geotextile,
            quantity=18000, unit_price=Decimal("90"),
            total_price=Decimal("1620000"), delivered_quantity=18000,
        )
    log("POs created: PO-2025-0001, PO-2025-0002")

    # ── Safety ────────────────────────────────────────────
    print("13. Creating safety records…")
    # Toolbox meetings: 3 per week
    tb_count = 0
    for d in work_dates:
        if d.weekday() not in (0, 2, 4): continue  # Mon, Wed, Fri
        topics = [
            "Working at Height – Fall Prevention",
            "Marine Safety & Life Jacket Usage",
            "Rock Placement Safety – Barge Operations",
            "Hot Work Permit Procedures",
            "Emergency Response & Evacuation",
            "Manual Handling & Ergonomics",
            "Chemical Safety – Geotextile Adhesives",
            "Heat Stress Prevention",
        ]
        _, c = ToolboxMeeting.objects.get_or_create(
            project=proj, meeting_date=d,
            defaults=dict(
                topic=rng.choice(topics),
                conducted_by=safety,
                location="Site Office - Breakwater BW-Ph2",
                attendee_count=rng.randint(20, 55),
                remarks="",
            )
        )
        if c: tb_count += 1
    log(f"Toolbox meetings created: {tb_count}")

    # Safety inspections
    insp_data = [
        (START_DATE + timedelta(days=7),  "Marine Safety", "Barge operation - no life ring on deck",     "Open"),
        (START_DATE + timedelta(days=21), "PPE",           "Missing PPE at rock placement area",         "Closed"),
        (START_DATE + timedelta(days=35), "Housekeeping",  "Debris and loose rocks on working deck",     "Closed"),
        (START_DATE + timedelta(days=50), "Working at Height", "Worker at height without safety harness","InProgress"),
        (START_DATE + timedelta(days=65), "Fire Safety",   "Fire extinguisher overdue for inspection",   "Closed"),
        (START_DATE + timedelta(days=80), "Edge Protection","Insufficient barricading at breakwater edge","Open"),
        (TODAY - timedelta(days=10),      "Health",        "Generator exhaust directed towards workers",  "Open"),
        (TODAY - timedelta(days=3),       "Equipment",     "Crane operator certificate log not on site",  "Open"),
    ]
    for insp_date, cat, finding, status in insp_data:
        SafetyInspection.objects.get_or_create(
            project=proj, inspection_date=insp_date,
            defaults=dict(
                inspector=safety, category=cat, finding=finding,
                location="Breakwater BW-Ph2",
                action_required="Immediate correction required" if status == "Open"
                                else "Corrected and verified by safety officer.",
                responsible_person="Site Engineer",
                due_date=insp_date + timedelta(days=7),
                status=status,
                close_date=insp_date + timedelta(days=5) if status == "Closed" else None,
            )
        )
    log(f"Safety inspections created: {len(insp_data)}")

    # Incidents
    IncidentReport.objects.get_or_create(
        project=proj,
        incident_date=START_DATE + timedelta(days=45),
        defaults=dict(
            type="NearMiss",
            description="Rock fell from crane load - no injury. Area was barricaded immediately.",
            location="Breakwater BW-Ph2 Sta.0+150",
            reported_by=safety,
            injured_person="",
            root_cause="Inadequate load securing procedure.",
            corrective_action="Updated lift plan and re-trained all riggers.",
            status="Closed",
        )
    )
    IncidentReport.objects.get_or_create(
        project=proj,
        incident_date=TODAY - timedelta(days=20),
        defaults=dict(
            type="FirstAid",
            description="Minor cut on hand - worker not wearing gloves during geotextile cutting.",
            location="Geotextile laying area",
            reported_by=safety,
            injured_person="Crew worker (anonymous)",
            root_cause="Non-compliance with PPE policy.",
            corrective_action="Mandatory glove checks reinforced before work commences.",
            status="Submitted",
        )
    )
    log("Incident reports created: 2")

    # ── Quality ───────────────────────────────────────────
    print("14. Creating quality records…")
    q_insp_data = [
        (START_DATE + timedelta(days=30),  "Core Rock Gradation Test",       "Approved", "Pass"),
        (START_DATE + timedelta(days=45),  "Foundation Preparation Check",   "Approved", "Pass"),
        (START_DATE + timedelta(days=60),  "Core Rock Layer Survey",         "Approved", "Pass"),
        (START_DATE + timedelta(days=90),  "Geotextile Overlapping Check",   "Rejected", "Fail"),
        (START_DATE + timedelta(days=110), "Armour Rock Placement Survey",   "Submitted", "Pending"),
        (TODAY - timedelta(days=7),        "Revetment Surface Level Check",  "Submitted", "Pending"),
        (TODAY - timedelta(days=2),        "Armour Rock Gradation Batch 3",  "Draft",    "Pending"),
    ]
    for insp_date, itype, status, result in q_insp_data:
        QualityInspection.objects.get_or_create(
            project=proj, inspection_date=insp_date, inspection_type=itype,
            defaults=dict(
                requested_by=eng, status=status, result=result,
                location="Breakwater BW-Ph2",
                station_or_chainage="Sta.0+000-0+450",
                description="Inspection per approved method statement and project specification.",
                remarks="As per approved method statement." if status == "Approved"
                        else ("Non-conformance - overlap insufficient." if status == "Rejected"
                              else "Pending client review."),
            )
        )
    log(f"Quality inspections created: {len(q_insp_data)}")

    # NCR
    NonConformanceReport.objects.get_or_create(
        project=proj, ncr_no="NCR-2026-001",
        defaults=dict(
            description="Geotextile overlap less than 500mm (found 320mm) at Sta.0+180–0+220",
            issued_date=START_DATE + timedelta(days=91),
            due_date=START_DATE + timedelta(days=105),
            responsible_person=eng,
            severity="High",
            status="Closed",
            root_cause="Crew not following approved method statement overlap specification.",
            corrective_action="Section removed and reinstalled with correct 600mm overlap. Re-inspection passed.",
            closed_date=START_DATE + timedelta(days=98),
        )
    )
    NonConformanceReport.objects.get_or_create(
        project=proj, ncr_no="NCR-2026-002",
        defaults=dict(
            description="Armour rock individual piece weight below specification (found 0.6T, spec >= 1T)",
            issued_date=TODAY - timedelta(days=12),
            due_date=TODAY + timedelta(days=14),
            responsible_person=eng,
            severity="High",
            status="Open",
            root_cause="Quarry supplied mixed-grade rock in batch 3.",
            corrective_action="Under review - supplier to replace non-conforming material.",
        )
    )
    log("NCR records created: NCR-2026-001 (Closed), NCR-2026-002 (Open)")

    # ── Cost Control ──────────────────────────────────────
    print("15. Creating cost control records…")
    cost_code_defs = [
        ("CC-01", "Marine Works",         "Direct"),
        ("CC-02", "Rock Materials",       "Direct"),
        ("CC-03", "Labour & Manpower",    "Direct"),
        ("CC-04", "Equipment & Plant",    "Direct"),
        ("CC-05", "Subcontract Works",    "Direct"),
        ("CC-06", "Site Establishment",   "Indirect"),
        ("CC-07", "Engineering & Survey", "Indirect"),
        ("CC-08", "Safety & HSE",         "Indirect"),
    ]
    cost_codes = {}
    for code, name, ctype in cost_code_defs:
        cc, _ = CostCode.objects.get_or_create(
            project=proj, code=code, defaults=dict(name=name, description=ctype)
        )
        cost_codes[code] = cc

    budget_defs = [
        ("CC-01", "Marine Works Budget",          28_000_000),
        ("CC-02", "Rock & Aggregate Materials",   42_000_000),
        ("CC-03", "Labour & Manpower Budget",     10_000_000),
        ("CC-04", "Equipment Hire Budget",         6_000_000),
        ("CC-05", "Subcontract (Geotextile)",      3_500_000),
        ("CC-06", "Site Establishment Budget",     2_000_000),
        ("CC-07", "Engineering & Survey Budget",   2_000_000),
        ("CC-08", "Safety Budget",                 1_500_000),
    ]
    for cc_code, desc, amount in budget_defs:
        cc = cost_codes.get(cc_code)
        if cc:
            BudgetItem.objects.get_or_create(
                project=proj, cost_code=cc,
                defaults=dict(description=desc, budget_amount=amount)
            )

    # Actual costs — monthly buckets
    actual_defs = [
        (date(2025, 11, 30), "CC-01", "Marine mobilization & barge hire Nov",   1_850_000),
        (date(2025, 12, 31), "CC-01", "Barge hire & marine ops Dec",            2_200_000),
        (date(2026,  1, 31), "CC-01", "Marine ops Jan",                         2_100_000),
        (date(2026,  2, 28), "CC-01", "Marine ops Feb",                         1_950_000),
        (date(2026,  3, 31), "CC-01", "Marine ops Mar",                         2_300_000),
        (date(2026,  4, 30), "CC-01", "Marine ops Apr",                         2_150_000),
        (date(2025, 11, 30), "CC-02", "Core rock delivery Nov",                 3_200_000),
        (date(2025, 12, 31), "CC-02", "Core rock delivery Dec",                 4_800_000),
        (date(2026,  1, 31), "CC-02", "Core rock delivery Jan",                 5_100_000),
        (date(2026,  2, 28), "CC-02", "Core rock + armour Feb",                 4_600_000),
        (date(2026,  3, 31), "CC-02", "Core + armour + geotextile Mar",         5_300_000),
        (date(2026,  4, 30), "CC-02", "Rock materials Apr",                     4_900_000),
        (date(2025, 11, 30), "CC-03", "Labour Nov",                               780_000),
        (date(2025, 12, 31), "CC-03", "Labour Dec",                               850_000),
        (date(2026,  1, 31), "CC-03", "Labour Jan",                               900_000),
        (date(2026,  2, 28), "CC-03", "Labour Feb",                               870_000),
        (date(2026,  3, 31), "CC-03", "Labour Mar",                               920_000),
        (date(2026,  4, 30), "CC-03", "Labour Apr",                               890_000),
        (date(2025, 12, 31), "CC-04", "Equipment hire Dec–Jan",                   450_000),
        (date(2026,  2, 28), "CC-04", "Equipment hire Feb–Mar",                   480_000),
        (date(2026,  4, 30), "CC-04", "Equipment hire Apr",                       390_000),
        (date(2026,  1, 31), "CC-05", "Geotextile subcontract payment 1",         900_000),
        (date(2026,  3, 31), "CC-05", "Geotextile subcontract payment 2",         850_000),
        (date(2025, 11, 30), "CC-06", "Site establishment Nov",                   750_000),
        (date(2026,  1, 31), "CC-07", "Survey & engineering Q1",                  380_000),
        (date(2026,  4, 30), "CC-07", "Survey & engineering Q2",                  360_000),
        (date(2025, 12, 31), "CC-08", "Safety equipment & training",              220_000),
        (date(2026,  3, 31), "CC-08", "Safety – HSE Q1",                          180_000),
    ]
    ac_count = 0
    for cost_date, cc_code, desc, amount in actual_defs:
        cc = cost_codes.get(cc_code)
        if not cc: continue
        _, c = ActualCost.objects.get_or_create(
            project=proj, cost_code=cc, description=desc,
            defaults=dict(amount=amount, cost_date=cost_date, created_by=admin, source_type="Other")
        )
        if c: ac_count += 1
    log(f"Budget items created: {len(budget_defs)}, Actual costs: {ac_count}")

    # ── Summary ───────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Scenario created successfully!")
    print(f"  Project : {proj.project_name}")
    print(f"  Contract: {proj.contract_no}")
    print(f"  Period  : {START_DATE} → {END_DATE}")
    print(f"  Value   : ฿{int(CONTRACT_VAL):,}")
    elapsed = (TODAY - START_DATE).days
    total   = (END_DATE - START_DATE).days
    print(f"  Timeline: Day {elapsed}/{total} ({elapsed/total*100:.0f}% elapsed)")
    print(f"  URL     : http://127.0.0.1:8000/projects/{proj.pk}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true", help="Delete scenario data")
    args = parser.parse_args()

    if args.delete:
        delete_scenario()
    else:
        run()
