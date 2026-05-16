from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Equipment, DailyEquipmentRecord, EquipmentPhoto


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'category', 'capacity', 'unit', 'registration_no', 'project', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-6'), Column('category', css_class='col-md-6')),
            Row(Column('capacity', css_class='col-md-4'), Column('unit', css_class='col-md-4'), Column('registration_no', css_class='col-md-4')),
            Row(Column('project', css_class='col-md-6'), Column('status', css_class='col-md-6')),
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )


class DailyEquipmentRecordForm(forms.ModelForm):
    class Meta:
        model = DailyEquipmentRecord
        fields = ['project', 'report', 'report_date', 'equipment', 'status', 'working_hours', 'remarks']
        widgets = {'report_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['report'].required = False
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('report_date', css_class='col-md-6')),
            Row(Column('equipment', css_class='col-md-4'), Column('status', css_class='col-md-4'), Column('working_hours', css_class='col-md-4')),
            'report', 'remarks',
            Submit('submit', 'Save Record', css_class='btn btn-primary'),
        )


class EquipmentPhotoForm(forms.ModelForm):
    class Meta:
        model = EquipmentPhoto
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'placeholder': 'Caption (optional)'}),
        }
