import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django; django.setup()

from apps.manpower.models import ManpowerCategory
from apps.equipment.models import Equipment
from apps.materials.models import Material
from apps.safety.models import SafetyInspection
from apps.boq.models import BOQItem
from apps.project_controls.models import RockDailyRecord, SandDailyRecord

print("ManpowerCategories:", list(ManpowerCategory.objects.values_list("name", flat=True)))
print("Equipment (active):")
for e in Equipment.objects.filter(status="Active")[:15]:
    print(f"  {e.pk}: {e.name} [{e.category}]")
print("Materials:")
for m in Material.objects.all():
    print(f"  {m.pk}: {m.name} ({m.unit}) cat={m.category}")
print("SafetyInspection statuses:", [c[0] for c in SafetyInspection._meta.get_field('status').choices])
print("BOQItem fields:", [f.name for f in BOQItem._meta.fields])
print("RockDailyRecord fields:", [f.name for f in RockDailyRecord._meta.fields])
