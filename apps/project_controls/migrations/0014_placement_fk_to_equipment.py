from django.db import migrations, models
import django.db.models.deletion


# Barge name → Equipment name mapping based on existing data
_BARGE_TO_EQUIPMENT = {
    'Bang Sapan 2': 'Bang Sapan 2',
    'MTP10': 'MTP 10',
    'MTP8': 'MTP 8',
    'Yuttachai': 'J.Yuttachai 1',
    'Wheel Loader': 'Wheel Loader',
    'Dump Truck': 'Dump Truck (10-wheel)',
    'Onshore Truck': 'Onshore Truck',
}


def migrate_to_equipment(apps, schema_editor):
    Barge = apps.get_model('project_controls', 'Barge')
    Equipment = apps.get_model('equipment', 'Equipment')
    EquipmentCategory = apps.get_model('equipment', 'EquipmentCategory')
    RockBargePlacement = apps.get_model('project_controls', 'RockBargePlacement')
    SandBargePlacement = apps.get_model('project_controls', 'SandBargePlacement')

    # Ensure a "Truck" category exists for creating Onshore Truck
    truck_cat, _ = EquipmentCategory.objects.get_or_create(
        name='Truck',
        defaults={'description': 'Land transport trucks'},
    )
    # Ensure Onshore Truck exists in Equipment
    Equipment.objects.get_or_create(
        name='Onshore Truck',
        defaults={'category': truck_cat, 'status': 'Active'},
    )

    equipment_by_name = {e.name: e for e in Equipment.objects.all()}

    barge_to_equip = {}
    for barge in Barge.objects.all():
        equip_name = _BARGE_TO_EQUIPMENT.get(barge.name)
        if equip_name and equip_name in equipment_by_name:
            barge_to_equip[barge.pk] = equipment_by_name[equip_name]

    for rp in RockBargePlacement.objects.all():
        equip = barge_to_equip.get(rp.barge_old_id)
        if equip:
            rp.barge_id = equip.pk
            rp.save(update_fields=['barge_id'])

    for sp in SandBargePlacement.objects.all():
        equip = barge_to_equip.get(sp.barge_old_id)
        if equip:
            sp.barge_id = equip.pk
            sp.save(update_fields=['barge_id'])


def reverse_to_barge(apps, schema_editor):
    Barge = apps.get_model('project_controls', 'Barge')
    Equipment = apps.get_model('equipment', 'Equipment')
    RockBargePlacement = apps.get_model('project_controls', 'RockBargePlacement')
    SandBargePlacement = apps.get_model('project_controls', 'SandBargePlacement')

    reverse_map = {v: k for k, v in _BARGE_TO_EQUIPMENT.items()}
    barge_by_name = {b.name: b for b in Barge.objects.all()}
    equip_by_id = {e.pk: e for e in Equipment.objects.all()}

    for rp in RockBargePlacement.objects.all():
        if rp.barge_id:
            equip = equip_by_id.get(rp.barge_id)
            if equip:
                barge_name = reverse_map.get(equip.name)
                barge = barge_by_name.get(barge_name) if barge_name else None
                if barge:
                    rp.barge_old_id = barge.pk
                    rp.save(update_fields=['barge_old_id'])

    for sp in SandBargePlacement.objects.all():
        if sp.barge_id:
            equip = equip_by_id.get(sp.barge_id)
            if equip:
                barge_name = reverse_map.get(equip.name)
                barge = barge_by_name.get(barge_name) if barge_name else None
                if barge:
                    sp.barge_old_id = barge.pk
                    sp.save(update_fields=['barge_old_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('project_controls', '0013_equipment_photos_and_barge_equipment_link'),
        ('equipment', '0002_equipment_photos_and_barge_equipment_link'),
    ]

    operations = [
        # Step 1: Drop unique_together constraints that reference 'barge'
        migrations.AlterUniqueTogether(
            name='rockbargeplacement',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='sandbargeplacement',
            unique_together=set(),
        ),

        # Step 2: Rename existing barge FK column → barge_old (preserves Barge FK data)
        migrations.RenameField(
            model_name='rockbargeplacement',
            old_name='barge',
            new_name='barge_old',
        ),
        migrations.RenameField(
            model_name='sandbargeplacement',
            old_name='barge',
            new_name='barge_old',
        ),

        # Step 3: Add new nullable barge FK → Equipment
        migrations.AddField(
            model_name='rockbargeplacement',
            name='barge',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='equipment.equipment',
            ),
        ),
        migrations.AddField(
            model_name='sandbargeplacement',
            name='barge',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='equipment.equipment',
            ),
        ),

        # Step 4: Migrate data from barge_old (Barge PKs) to barge (Equipment PKs)
        migrations.RunPython(migrate_to_equipment, reverse_to_barge),

        # Step 5: Remove old barge_old FK columns
        migrations.RemoveField(
            model_name='rockbargeplacement',
            name='barge_old',
        ),
        migrations.RemoveField(
            model_name='sandbargeplacement',
            name='barge_old',
        ),

        # Step 6: Restore unique_together
        migrations.AlterUniqueTogether(
            name='rockbargeplacement',
            unique_together={('record', 'barge')},
        ),
        migrations.AlterUniqueTogether(
            name='sandbargeplacement',
            unique_together={('record', 'barge')},
        ),
    ]
