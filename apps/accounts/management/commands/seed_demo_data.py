from datetime import date, timedelta
from decimal import Decimal
import random
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Seed demo data for Construction ERP'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')
        with transaction.atomic():
            self._create_users()
            self._create_categories()
            project = self._create_project()
            materials = self._create_materials()
            equipment_list = self._create_equipment(project)
            boq_items = self._create_boq(project)
            self._create_daily_records(project, boq_items, materials, equipment_list)
            self._create_safety_records(project)
        self.stdout.write(self.style.SUCCESS(
            '\nDemo data loaded. Login at http://127.0.0.1:8000/\n'
            'Admin: admin / Demo@1234'
        ))

    def _create_users(self):
        from apps.accounts.models import User, UserProfile
        users_data = [
            ('admin', 'Admin', 'User', 'admin'),
            ('pm_john', 'John', 'Smith', 'project_manager'),
            ('eng_sara', 'Sara', 'Lee', 'site_engineer'),
            ('qs_mike', 'Mike', 'Brown', 'quantity_surveyor'),
            ('safety_ann', 'Ann', 'Chu', 'safety_officer'),
            ('store_bob', 'Bob', 'Green', 'storekeeper'),
            ('viewer_tom', 'Tom', 'White', 'viewer'),
        ]
        for username, first, last, role in users_data:
            if not User.objects.filter(username=username).exists():
                is_staff = role == 'admin'
                is_super = role == 'admin'
                u = User.objects.create_user(
                    username=username,
                    password='Demo@1234',
                    first_name=first,
                    last_name=last,
                    email=f'{username}@demo.construction',
                    role=role,
                    is_staff=is_staff,
                    is_superuser=is_super,
                )
                UserProfile.objects.get_or_create(user=u, defaults={'company': 'Demo Construction Co.', 'position': role})
                self.stdout.write(f'  Created user: {username}')

    def _create_categories(self):
        from apps.manpower.models import ManpowerCategory
        from apps.equipment.models import EquipmentCategory
        from apps.materials.models import MaterialCategory
        from apps.documents.models import DocumentCategory

        for name in ['Engineer', 'Foreman', 'Surveyor', 'SafetyOfficer', 'Operator', 'Driver', 'GeneralWorker', 'Other']:
            ManpowerCategory.objects.get_or_create(name=name)

        for name in ['Excavator', 'Loader', 'Truck', 'Crane', 'Barge', 'Generator', 'Pump', 'Compactor']:
            EquipmentCategory.objects.get_or_create(name=name)

        for name in ['Aggregate', 'Rock', 'Geotextile', 'Steel', 'Concrete', 'Pipe']:
            MaterialCategory.objects.get_or_create(name=name)

        for name in ['Drawing', 'Specification', 'Report', 'Correspondence', 'Certificate']:
            DocumentCategory.objects.get_or_create(name=name)

    def _create_project(self):
        from apps.accounts.models import User
        from apps.projects.models import Project, WorkArea, Stakeholder
        admin = User.objects.get(username='admin')
        project, created = Project.objects.get_or_create(
            contract_no='CON-2024-001',
            defaults={
                'project_name': 'Port Expansion Project Phase 1',
                'owner': 'Port Authority of Thailand',
                'contractor': 'Demo Construction Co., Ltd.',
                'consultant': 'Engineering Consultants International',
                'location': 'Laem Chabang, Chonburi, Thailand',
                'start_date': date(2024, 1, 1),
                'finish_date': date(2025, 6, 30),
                'contract_value': Decimal('150000000.00'),
                'description': 'Construction of new port expansion including breakwater, quay wall, and yard facilities.',
                'status': 'Active',
                'created_by': admin,
            }
        )
        if created:
            for wa_name in ['Zone A – Breakwater', 'Zone B – Quay Wall', 'Zone C – Yard', 'Zone D – Access Road']:
                WorkArea.objects.get_or_create(project=project, name=wa_name)

            Stakeholder.objects.get_or_create(
                project=project, name='Mr. Somchai Phongpaisal',
                defaults={'company': 'Port Authority of Thailand', 'role': 'Project Director', 'email': 'somchai@pat.go.th', 'is_primary': True}
            )
            Stakeholder.objects.get_or_create(
                project=project, name='Mr. John Smith',
                defaults={'company': 'Demo Construction Co.', 'role': 'Project Manager', 'email': 'pm_john@demo.construction', 'is_primary': False}
            )
        return project

    def _create_materials(self):
        from apps.materials.models import MaterialCategory, Material
        materials_data = [
            ('Sand', 'Aggregate', 'm³', '1.600'),
            ('Core Rock (300-500kg)', 'Rock', 'Ton', '1.000'),
            ('Armour Rock (1-3T)', 'Rock', 'Ton', '1.000'),
            ('Geotextile', 'Geotextile', 'm²', '0.001'),
            ('Steel Pipe Pile', 'Steel', 'm', '0.050'),
            ('Concrete Barrier', 'Concrete', 'nos', '0.500'),
        ]
        materials = []
        for name, cat_name, unit, weight in materials_data:
            cat = MaterialCategory.objects.get(name=cat_name)
            mat, _ = Material.objects.get_or_create(
                name=name,
                defaults={'category': cat, 'unit': unit, 'unit_weight': Decimal(weight)}
            )
            materials.append(mat)
        return materials

    def _create_equipment(self, project):
        from apps.equipment.models import EquipmentCategory, Equipment
        equipment_data = [
            ('Excavator (CAT 320)', 'Excavator', '0.9 m³', 'Bucket', 'CAT-320-001'),
            ('Wheel Loader', 'Loader', '2.5 m³', 'Bucket', 'WL-001'),
            ('Dump Truck (10-wheel)', 'Truck', '10 m³', 'Load', 'DT-001'),
            ('Crane (50T)', 'Crane', '50 Ton', 'Cap', 'CR-50-001'),
            ('Split Barge (500T)', 'Barge', '500 m³', 'Cap', 'SB-500-001'),
            ('Generator (200kVA)', 'Generator', '200 kVA', 'kVA', 'GEN-200-001'),
        ]
        equips = []
        for name, cat_name, capacity, unit, reg_no in equipment_data:
            cat = EquipmentCategory.objects.get(name=cat_name)
            eq, _ = Equipment.objects.get_or_create(
                registration_no=reg_no,
                defaults={'name': name, 'category': cat, 'capacity': capacity, 'unit': unit, 'project': project, 'status': 'Active'}
            )
            equips.append(eq)
        return equips

    def _create_boq(self, project):
        from apps.boq.models import BOQItem
        boq_data = [
            ('1.1', 'Mobilization & Demobilization', 'LS', '1.000', '2500000.00'),
            ('2.1', 'Temporary Works & Cofferdams', 'm²', '2000.000', '1200.00'),
            ('3.1', 'Dredging & Excavation', 'm³', '50000.000', '250.00'),
            ('3.2', 'Disposal of Dredged Material', 'm³', '50000.000', '80.00'),
            ('4.1', 'Core Rock Supply & Placement', 'Ton', '120000.000', '450.00'),
            ('4.2', 'Armour Rock Supply & Placement', 'Ton', '45000.000', '850.00'),
            ('4.3', 'Geotextile Filter Layer', 'm²', '85000.000', '120.00'),
            ('5.1', 'Concrete Quay Wall (Precast)', 'm', '600.000', '35000.00'),
            ('5.2', 'Steel Pipe Pile Driving', 'm', '8000.000', '2200.00'),
            ('6.1', 'Yard Pavement & Drainage', 'm²', '25000.000', '800.00'),
        ]
        items = []
        for item_no, desc, unit, qty, rate in boq_data:
            item, _ = BOQItem.objects.get_or_create(
                project=project, item_no=item_no,
                defaults={'description': desc, 'unit': unit, 'contract_quantity': Decimal(qty), 'unit_rate': Decimal(rate)}
            )
            items.append(item)
        return items

    def _create_daily_records(self, project, boq_items, materials, equipment_list):
        from apps.accounts.models import User
        from apps.manpower.models import ManpowerCategory, DailyManpowerRecord
        from apps.equipment.models import DailyEquipmentRecord
        from apps.materials.models import MaterialDelivery
        from apps.boq.models import DailyProgressRecord
        from apps.daily_reports.models import DailyReport

        eng_sara = User.objects.get(username='eng_sara')
        pm_john = User.objects.get(username='pm_john')
        cats = list(ManpowerCategory.objects.all())
        today = date.today()
        start = today - timedelta(days=29)

        manpower_plan = {
            'Engineer': 3, 'Foreman': 4, 'Operator': 6, 'Driver': 8,
            'GeneralWorker': 40, 'SafetyOfficer': 2, 'Surveyor': 2, 'Other': 5
        }

        for i in range(30):
            d = start + timedelta(days=i)
            report, created = DailyReport.objects.get_or_create(
                project=project, report_date=d,
                defaults={
                    'weather_morning': random.choice(['Sunny', 'Partly Cloudy', 'Cloudy']),
                    'weather_afternoon': random.choice(['Sunny', 'Partly Cloudy', 'Rainy']),
                    'prepared_by': eng_sara,
                    'checked_by': pm_john,
                    'status': 'Approved' if i < 25 else 'Draft',
                    'remarks': f'Day {i+1} operations. Works progressing as planned.',
                }
            )

            for cat in cats:
                qty = manpower_plan.get(cat.name, 5)
                qty = max(1, qty + random.randint(-2, 2))
                DailyManpowerRecord.objects.get_or_create(
                    project=project, report=report, report_date=d, category=cat,
                    defaults={'company': 'Demo Construction Co.', 'quantity': qty}
                )

            for eq in equipment_list:
                status = 'Working' if random.random() > 0.15 else random.choice(['Standby', 'Breakdown'])
                hours = Decimal(str(round(random.uniform(6, 10), 1))) if status == 'Working' else Decimal('0')
                DailyEquipmentRecord.objects.get_or_create(
                    project=project, report=report, report_date=d, equipment=eq,
                    defaults={'status': status, 'working_hours': hours}
                )

            if i % 3 == 0:
                mat = random.choice(materials[:3])
                qty = Decimal(str(round(random.uniform(50, 500), 1)))
                MaterialDelivery.objects.get_or_create(
                    project=project, delivery_date=d, material=mat,
                    delivery_note_no=f'DN-{d.strftime("%Y%m%d")}-{random.randint(100,999)}',
                    defaults={
                        'truck_no': f'กข-{random.randint(1000,9999)}',
                        'quantity': qty,
                        'unit_price': Decimal(str(round(random.uniform(400, 900), 2))),
                        'source': 'Demo Quarry Co., Ltd.',
                    }
                )

            for item in boq_items[2:5]:
                daily_qty = Decimal(str(round(random.uniform(50, 300), 1)))
                if not DailyProgressRecord.objects.filter(project=project, boq_item=item, record_date=d).exists():
                    cum = item.cumulative_quantity
                    if cum < item.contract_quantity:
                        remaining = item.contract_quantity - cum
                        daily_qty = min(daily_qty, remaining)
                        if daily_qty > 0:
                            DailyProgressRecord.objects.create(
                                project=project, boq_item=item, record_date=d,
                                daily_quantity=daily_qty, allow_overrun=False
                            )

    def _create_safety_records(self, project):
        from apps.accounts.models import User
        from apps.safety.models import ToolboxMeeting, SafetyInspection, IncidentReport
        safety_ann = User.objects.get(username='safety_ann')
        today = date.today()

        for i, topic in enumerate(['Working at Heights', 'Marine Safety', 'PPE Usage']):
            ToolboxMeeting.objects.get_or_create(
                project=project, meeting_date=today - timedelta(days=i*5),
                topic=topic,
                defaults={
                    'location': 'Site Office',
                    'conducted_by': safety_ann,
                    'attendee_count': random.randint(15, 40),
                    'remarks': f'Toolbox meeting on {topic}.',
                }
            )

        for i, (cat, finding) in enumerate([
            ('Housekeeping', 'Material improperly stored near work area'),
            ('PPE', 'Worker observed without safety helmet'),
        ]):
            SafetyInspection.objects.get_or_create(
                project=project, inspection_date=today - timedelta(days=i*3+1),
                category=cat, finding=finding,
                defaults={
                    'location': 'Zone A – Breakwater',
                    'inspector': safety_ann,
                    'action_required': 'Immediate corrective action required',
                    'responsible_person': 'Site Foreman',
                    'due_date': today + timedelta(days=3),
                    'status': 'Open',
                }
            )

        IncidentReport.objects.get_or_create(
            project=project,
            incident_date=today - timedelta(days=7),
            type='NearMiss',
            defaults={
                'incident_time': None,
                'location': 'Zone B – Quay Wall',
                'description': 'Near miss: Unsecured load swung near workers during crane operation.',
                'root_cause': 'Inadequate banksman communication.',
                'corrective_action': 'Refresher training on lifting operations conducted.',
                'reported_by': safety_ann,
                'status': 'Closed',
            }
        )
