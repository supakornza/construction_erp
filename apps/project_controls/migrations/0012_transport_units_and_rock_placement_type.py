from django.db import migrations, models


ONSHORE_UNITS = [
    ('OT', 'Onshore Truck', 'Onshore'),
    ('WL', 'Wheel Loader', 'Onshore'),
    ('DT', 'Dump Truck', 'Onshore'),
]


def seed_onshore_transport_units(apps, schema_editor):
    Barge = apps.get_model('project_controls', 'Barge')
    Barge.objects.filter(transport_mode='').update(transport_mode='Offshore')
    for code, name, mode in ONSHORE_UNITS:
        Barge.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'transport_mode': mode,
                'is_active': True,
            },
        )


def unseed_onshore_transport_units(apps, schema_editor):
    Barge = apps.get_model('project_controls', 'Barge')
    Barge.objects.filter(code__in=[code for code, _, _ in ONSHORE_UNITS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('project_controls', '0011_project_action_register'),
    ]

    operations = [
        migrations.AddField(
            model_name='barge',
            name='transport_mode',
            field=models.CharField(
                choices=[('Offshore', 'Offshore'), ('Onshore', 'Onshore'), ('Both', 'Both')],
                default='Offshore',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='rockbargeplacement',
            name='placement_type',
            field=models.CharField(
                choices=[('Offshore', 'Offshore'), ('Onshore', 'Onshore')],
                default='Offshore',
                max_length=20,
            ),
        ),
        migrations.RunPython(seed_onshore_transport_units, unseed_onshore_transport_units),
    ]
