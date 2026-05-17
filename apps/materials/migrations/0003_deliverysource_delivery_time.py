from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0002_materialdelivery_destination'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliverySource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='ชื่อแหล่งวัสดุ')),
                ('description', models.CharField(blank=True, max_length=300, verbose_name='รายละเอียด')),
            ],
            options={
                'verbose_name': 'แหล่งวัสดุ',
                'verbose_name_plural': 'แหล่งวัสดุ',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='materialdelivery',
            name='delivery_time',
            field=models.TimeField(blank=True, null=True, verbose_name='เวลารับ'),
        ),
    ]
