from django.db import models
from apps.projects.models import Project


class ManpowerCategory(models.Model):
    NAME_CHOICES = [
        ('CivilEngineer',        'Civil Engineer (CE)'),
        ('MechanicalEngineer',   'Mechanical Engineer (ME)'),
        ('ElectricalEngineer',   'Electrical Engineer (EE)'),
        ('Foreman',              'Foreman / Supervisor'),
        ('Technician',           'Technician / QC Inspector'),
        ('SafetyOfficer',        'Safety Officer (จ.ป.)'),
        ('Headman',              'Headman / Gang Leader'),
        ('Carpenter',            'Carpenter'),
        ('Mason',                'Mason'),
        ('SteelWorker',          'Steel Worker'),
        ('Fitter',               'Fitter / Assistant'),
        ('Welder',               'Welder'),
        ('Electrician',          'Electrician'),
        ('Surveyor',             'Surveyor'),
        ('EquipmentOperator',    'Equipment Operator'),
        ('GeneralWorker',        'General Worker / Laborer'),
        ('Driver',               'Driver'),
        ('Mechanic',             'Mechanic (MC)'),
    ]

    NAME_TH_MAP = {
        'CivilEngineer':        'วิศวกร CE',
        'MechanicalEngineer':   'วิศวกร ME',
        'ElectricalEngineer':   'วิศวกร EE',
        'Foreman':              'โฟร์แมน/Supervisor',
        'Technician':           'ช่างเทคนิค/QC',
        'SafetyOfficer':        'จ.ป.',
        'Headman':              'หัวหน้าชุด/Headman',
        'Carpenter':            'ช่างไม้',
        'Mason':                'ช่างปูน',
        'SteelWorker':          'ช่างเหล็ก',
        'Fitter':               'ช่างประกอบ/ผู้ช่วย',
        'Welder':               'ช่างเชื่อม',
        'Electrician':          'ช่างไฟฟ้า',
        'Surveyor':             'ช่างสำรวจ',
        'EquipmentOperator':    'คนขับเครื่องจักร',
        'GeneralWorker':        'คนงานทั่วไป',
        'Driver':               'พนักงานขับรถ',
        'Mechanic':             'ช่างแมคคานิค (MC)',
    }

    SORT_ORDER = [
        'CivilEngineer', 'MechanicalEngineer', 'ElectricalEngineer',
        'Foreman', 'Technician', 'SafetyOfficer', 'Headman',
        'Carpenter', 'Mason', 'SteelWorker', 'Fitter', 'Welder',
        'Electrician', 'Surveyor', 'EquipmentOperator',
        'GeneralWorker', 'Driver', 'Mechanic',
    ]

    name = models.CharField(max_length=50, choices=NAME_CHOICES, unique=True)
    name_th = models.CharField(max_length=100, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Manpower Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.get_name_display()

    @property
    def display_th(self):
        return self.name_th or self.NAME_TH_MAP.get(self.name, self.name)


class DailyManpowerRecord(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='manpower_records')
    report = models.ForeignKey('daily_reports.DailyReport', on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='manpower_records')
    report_date = models.DateField()
    category = models.ForeignKey(ManpowerCategory, on_delete=models.PROTECT)
    company = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-report_date', 'category__sort_order']

    def __str__(self):
        return f"{self.project.contract_no} – {self.category} – {self.report_date} – {self.quantity}"
