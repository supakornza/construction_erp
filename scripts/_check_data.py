import django, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.projects.models import Project
from apps.boq.models import BOQItem
from apps.materials.models import Material, MaterialCategory
from apps.equipment.models import Equipment, EquipmentCategory
from apps.procurement.models import Supplier
from apps.accounts.models import User

print("=== Current Data ===")
print("Projects:", Project.objects.count())
for p in Project.objects.all():
    print(f"  - {p.pk}: {p.contract_no} | {p.project_name} | {p.status}")
print("BOQ Items:", BOQItem.objects.count())
print("Material Categories:", list(MaterialCategory.objects.values_list("name", flat=True)))
print("Equipment Categories:", list(EquipmentCategory.objects.values_list("name", flat=True)))
print("Suppliers:", Supplier.objects.count())
for s in Supplier.objects.all()[:5]:
    print(f"  - {s.pk}: {s.name}")
print("Users:", User.objects.count())
for u in User.objects.filter(is_active=True)[:5]:
    print(f"  - {u.pk}: {u.username} | {u.get_full_name()}")
