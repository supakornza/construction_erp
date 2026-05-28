import re

import django.utils.timezone
from django.db import migrations, models


def migrate_project_action_register(apps, schema_editor):
    ProjectActionPlan = apps.get_model('project_controls', 'ProjectActionPlan')
    ProjectActionItem = apps.get_model('project_controls', 'ProjectActionItem')

    counters = {}
    for plan in ProjectActionPlan.objects.order_by('project_id', 'id'):
        project_id = plan.project_id
        counters.setdefault(project_id, 0)

        existing_id = plan.action_id or ''
        match = re.fullmatch(r'ACT-(\d+)', existing_id)
        if match:
            counters[project_id] = max(counters[project_id], int(match.group(1)))
            action_id = existing_id
        else:
            counters[project_id] += 1
            action_id = f'ACT-{counters[project_id]:03d}'

        item_lines = []
        for item in ProjectActionItem.objects.filter(action_plan_id=plan.id).order_by('item_no'):
            target = item.target_date.isoformat() if item.target_date else '-'
            responsible = item.responsible_party or '-'
            item_lines.append(
                f'{item.item_no}: {item.action} | Responsible: {responsible} | Target: {target} | Status: {item.status}'
            )

        legacy_notes = []
        if getattr(plan, 'description', ''):
            legacy_notes.append(plan.description)
        if getattr(plan, 'root_cause', ''):
            legacy_notes.append(f'Root Cause: {plan.root_cause}')
        if getattr(plan, 'impact', ''):
            legacy_notes.append(f'Impact: {plan.impact}')
        legacy_notes.extend(item_lines)

        status_map = {
            'Waiting': 'Pending',
            'Resolved': 'Finish',
            'Closed': 'Finish',
        }
        category_map = {
            'Coordination': 'Coordination',
        }

        plan.action_id = action_id
        plan.date_raised = plan.created_at.date() if plan.created_at else django.utils.timezone.localdate()
        plan.description_th = plan.title or ''
        plan.responsible_parties = plan.owner or ''
        plan.status = status_map.get(plan.status, plan.status)
        plan.category = category_map.get(plan.category, 'Other')
        plan.remarks = '\n'.join(part for part in legacy_notes if part)
        plan.save(update_fields=[
            'action_id', 'date_raised', 'description_th', 'responsible_parties',
            'status', 'category', 'remarks',
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('project_controls', '0010_projectactionplan_projectactionitem_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='projectactionplan',
            options={'ordering': ['action_id']},
        ),
        migrations.AddField(
            model_name='projectactionplan',
            name='action_id',
            field=models.CharField(blank=True, default='', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='projectactionplan',
            name='date_raised',
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
        migrations.AddField(
            model_name='projectactionplan',
            name='description_th',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='projectactionplan',
            name='responsible_parties',
            field=models.CharField(blank=True, default='', max_length=300),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='projectactionplan',
            name='meeting_reference',
            field=models.CharField(blank=True, default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='projectactionplan',
            name='remarks',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='projectactionplan',
            name='category',
            field=models.CharField(choices=[
                ('Technical', 'Technical'),
                ('Documentation', 'Documentation'),
                ('Regulatory', 'Regulatory'),
                ('Safety', 'Safety'),
                ('Site Management', 'Site Management'),
                ('Security', 'Security'),
                ('Coordination', 'Coordination'),
                ('Commercial', 'Commercial'),
                ('Other', 'Other'),
            ], default='Other', max_length=30),
        ),
        migrations.AlterField(
            model_name='projectactionplan',
            name='priority',
            field=models.CharField(choices=[
                ('High', 'High'),
                ('Medium', 'Medium'),
                ('Low', 'Low'),
                ('Critical', 'Critical'),
            ], default='Medium', max_length=20),
        ),
        migrations.AlterField(
            model_name='projectactionplan',
            name='status',
            field=models.CharField(choices=[
                ('Open', 'Open'),
                ('In Progress', 'In Progress'),
                ('Pending', 'Pending'),
                ('Finish', 'Finish'),
                ('Cancelled', 'Cancelled'),
            ], default='Open', max_length=20),
        ),
        migrations.RunPython(migrate_project_action_register, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='projectactionplan',
            name='closed_date',
        ),
        migrations.RemoveField(
            model_name='projectactionplan',
            name='description',
        ),
        migrations.RemoveField(
            model_name='projectactionplan',
            name='impact',
        ),
        migrations.RemoveField(
            model_name='projectactionplan',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='projectactionplan',
            name='root_cause',
        ),
        migrations.RemoveField(
            model_name='projectactionplan',
            name='title',
        ),
        migrations.DeleteModel(
            name='ProjectActionItem',
        ),
        migrations.AlterUniqueTogether(
            name='projectactionplan',
            unique_together={('project', 'action_id')},
        ),
    ]
