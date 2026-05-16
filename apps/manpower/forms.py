from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import DailyManpowerRecord


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
