from django.db import migrations, models


def backfill_sand_source(apps, schema_editor):
    SandDailyRecord = apps.get_model('project_controls', 'SandDailyRecord')
    SandDailyRecord.objects.filter(sand_source='').update(sand_source='Oswald')


class Migration(migrations.Migration):

    dependencies = [
        ('project_controls', '0002_seed_barges'),
    ]

    operations = [
        migrations.AddField(
            model_name='sanddailyrecord',
            name='sand_source',
            field=models.CharField(blank=True, default='Oswald', max_length=200),
        ),
        migrations.RunPython(backfill_sand_source, migrations.RunPython.noop),
    ]
