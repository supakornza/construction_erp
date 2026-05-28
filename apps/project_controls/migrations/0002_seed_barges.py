from decimal import Decimal

from django.db import migrations


BARGES = [
    ('B1', 'Yuttachai', None),
    ('B2', 'Bang Sapan 2', None),
    ('B3', 'MTP10', None),
    ('B4', 'MTP8', None),
]


def seed_barges(apps, schema_editor):
    Barge = apps.get_model('project_controls', 'Barge')
    for code, name, capacity_ton in BARGES:
        defaults = {'name': name, 'is_active': True}
        if capacity_ton is not None:
            defaults['capacity_ton'] = Decimal(str(capacity_ton))
        Barge.objects.update_or_create(code=code, defaults=defaults)


def unseed_barges(apps, schema_editor):
    Barge = apps.get_model('project_controls', 'Barge')
    Barge.objects.filter(code__in=[code for code, _, _ in BARGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('project_controls', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_barges, unseed_barges),
    ]
