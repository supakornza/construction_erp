from django.db import migrations

CATEGORIES = [
    ('CivilEngineer',       'วิศวกร CE',              0),
    ('MechanicalEngineer',  'วิศวกร ME',              1),
    ('ElectricalEngineer',  'วิศวกร EE',              2),
    ('Foreman',             'โฟร์แมน/Supervisor',     3),
    ('Technician',          'ช่างเทคนิค/QC',          4),
    ('SafetyOfficer',       'จ.ป.',                   5),
    ('Headman',             'หัวหน้าชุด/Headman',     6),
    ('Carpenter',           'ช่างไม้',                7),
    ('Mason',               'ช่างปูน',               8),
    ('SteelWorker',         'ช่างเหล็ก',              9),
    ('Fitter',              'ช่างประกอบ/ผู้ช่วย',    10),
    ('Welder',              'ช่างเชื่อม',            11),
    ('Electrician',         'ช่างไฟฟ้า',             12),
    ('Surveyor',            'ช่างสำรวจ',             13),
    ('EquipmentOperator',   'คนขับเครื่องจักร',      14),
    ('GeneralWorker',       'คนงานทั่วไป',           15),
    ('Driver',              'พนักงานขับรถ',          16),
    ('Mechanic',            'ช่างแมคคานิค (MC)',     17),
]

OLD_TO_NEW = {
    'Engineer':      'CivilEngineer',
    'Foreman':       'Foreman',
    'Surveyor':      'Surveyor',
    'SafetyOfficer': 'SafetyOfficer',
    'Operator':      'EquipmentOperator',
    'Driver':        'Driver',
    'GeneralWorker': 'GeneralWorker',
    'Other':         'GeneralWorker',
}


def populate_categories(apps, schema_editor):
    ManpowerCategory = apps.get_model('manpower', 'ManpowerCategory')
    DailyManpowerRecord = apps.get_model('manpower', 'DailyManpowerRecord')

    # Remap existing records from old categories to new keys before deleting
    for old_name, new_name in OLD_TO_NEW.items():
        old_qs = ManpowerCategory.objects.filter(name=old_name)
        if not old_qs.exists():
            continue
        old_cat = old_qs.first()
        # Ensure target new category exists
        new_cat, _ = ManpowerCategory.objects.get_or_create(name=new_name)
        if old_cat.pk != new_cat.pk:
            DailyManpowerRecord.objects.filter(category=old_cat).update(category=new_cat)
            old_cat.delete()

    # Create/update all 18 categories with correct name_th and sort_order
    for name, name_th, sort_order in CATEGORIES:
        ManpowerCategory.objects.update_or_create(
            name=name,
            defaults={'name_th': name_th, 'sort_order': sort_order},
        )

    # Remove any leftover unknown categories that have no records
    valid_names = {c[0] for c in CATEGORIES}
    ManpowerCategory.objects.exclude(name__in=valid_names).filter(
        dailymanpowerrecord=None
    ).delete()


def reverse_populate(apps, schema_editor):
    pass  # irreversible cleanup; accept data loss on reverse


class Migration(migrations.Migration):

    dependencies = [
        ('manpower', '0002_update_categories_18roles'),
    ]

    operations = [
        migrations.RunPython(populate_categories, reverse_populate),
    ]
