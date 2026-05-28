import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0003_deliverysource_delivery_time'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='materialdelivery',
            name='source_area',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='source_deliveries',
                to='projects.workarea',
                verbose_name='แหล่งวัสดุ (Work Area)',
            ),
        ),
    ]
