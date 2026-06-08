from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import DailyManpowerRecord, ManpowerCategory


class BulkManpowerHeaderForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=None,
        label='โครงการ / Project',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    report_date = forms.DateField(
        label='วันที่ / Date',
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
    )
    company = forms.CharField(
        max_length=200,
        label='บริษัท/ผู้รับเหมา / Company',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, project_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.projects.models import Project
        self.fields['project'].queryset = project_queryset or Project.objects.filter(status='Active').order_by('contract_no')


class DailyManpowerRecordForm(forms.ModelForm):
    class Meta:
        model = DailyManpowerRecord
        fields = ['project', 'report', 'report_date', 'category', 'company', 'quantity', 'remarks']
        widgets = {'report_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['report'].required = False
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('report_date', css_class='col-md-6')),
            Row(Column('category', css_class='col-md-4'), Column('company', css_class='col-md-4'), Column('quantity', css_class='col-md-4')),
            'report',
            'remarks',
            Submit('submit', 'Save Record', css_class='btn btn-primary'),
        )
