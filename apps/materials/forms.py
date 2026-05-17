import json
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from apps.projects.models import WorkArea
from .models import Material, MaterialDelivery, MaterialUsage


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'category', 'unit', 'unit_weight', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-6'), Column('category', css_class='col-md-6')),
            Row(Column('unit', css_class='col-md-6'), Column('unit_weight', css_class='col-md-6')),
            'description',
            Submit('submit', 'บันทึก', css_class='btn btn-primary'),
        )


class MaterialDeliveryForm(forms.ModelForm):
    class Meta:
        model = MaterialDelivery
        fields = [
            'project', 'delivery_date', 'delivery_time',
            'material', 'quantity', 'unit_price',
            'source_area', 'destination',
            'delivery_note_no', 'truck_no',
            'remarks',
        ]
        labels = {
            'project': 'โครงการ',
            'delivery_date': 'วันที่รับวัสดุ',
            'delivery_time': 'เวลารับ',
            'material': 'วัสดุ',
            'quantity': 'ปริมาณ',
            'unit_price': 'ราคาต่อหน่วย (บาท)',
            'source_area': 'แหล่งวัสดุ (Work Area)',
            'destination': 'ปลายทาง (กอง/พื้นที่)',
            'delivery_note_no': 'เลขที่ใบส่งของ',
            'truck_no': 'ทะเบียนรถ',
            'remarks': 'หมายเหตุ',
        }
        widgets = {
            'delivery_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'delivery_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        wa_qs = WorkArea.objects.select_related('project').order_by('project__contract_no', 'name')

        # source_area — WorkArea dropdown (same as destination)
        self.fields['source_area'].queryset = wa_qs
        self.fields['source_area'].empty_label = '— เลือกแหล่งวัสดุ —'

        # destination — WorkArea dropdown
        self.fields['destination'].queryset = wa_qs
        self.fields['destination'].empty_label = '— เลือกปลายทาง —'

        # Serialize work areas for JS project-based filtering (shared by both dropdowns)
        work_areas = list(WorkArea.objects.values('id', 'project_id', 'name'))
        self.work_areas_json = json.dumps(work_areas)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<div class="border rounded p-3 mb-3 bg-light"><div class="fw-semibold text-primary mb-2"><i class="fas fa-folder-open me-1"></i>ข้อมูลทั่วไป</div>'),
            Row(Column('project', css_class='col-md-8'), Column('delivery_date', css_class='col-md-2'), Column('delivery_time', css_class='col-md-2')),
            HTML('</div>'),

            HTML('<div class="border rounded p-3 mb-3 bg-light"><div class="fw-semibold text-success mb-2"><i class="fas fa-boxes-stacking me-1"></i>ข้อมูลวัสดุ</div>'),
            Row(Column('material', css_class='col-md-6'), Column('quantity', css_class='col-md-3'), Column('unit_price', css_class='col-md-3')),
            HTML('</div>'),

            HTML('<div class="border rounded p-3 mb-3 bg-light"><div class="fw-semibold text-warning mb-2"><i class="fas fa-route me-1"></i>ต้นทาง / ปลายทาง</div>'),
            Row(Column('source_area', css_class='col-md-6'), Column('destination', css_class='col-md-6')),
            HTML('</div>'),

            HTML('<div class="border rounded p-3 mb-3 bg-light"><div class="fw-semibold text-info mb-2"><i class="fas fa-truck me-1"></i>ข้อมูลการขนส่ง</div>'),
            Row(Column('truck_no', css_class='col-md-6'), Column('delivery_note_no', css_class='col-md-6')),
            HTML('</div>'),

            'remarks',
            Submit('submit', 'บันทึกการรับวัสดุ', css_class='btn btn-primary btn-lg w-100 mt-2'),
        )


class MaterialUsageForm(forms.ModelForm):
    class Meta:
        model = MaterialUsage
        fields = ['project', 'usage_date', 'material', 'work_area', 'quantity', 'remarks']
        widgets = {'usage_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('usage_date', css_class='col-md-6')),
            Row(Column('material', css_class='col-md-4'), Column('work_area', css_class='col-md-4'), Column('quantity', css_class='col-md-4')),
            'remarks',
            Submit('submit', 'บันทึกการใช้วัสดุ', css_class='btn btn-primary'),
        )
