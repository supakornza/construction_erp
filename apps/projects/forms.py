from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from .models import Project, Stakeholder, WorkArea


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['project_name', 'contract_no', 'owner', 'contractor', 'consultant',
                  'location', 'start_date', 'finish_date', 'contract_value', 'description', 'status']
        widgets = {
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'finish_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Project Information',
                Row(Column('project_name', css_class='col-md-8'), Column('contract_no', css_class='col-md-4')),
                Row(Column('owner', css_class='col-md-4'), Column('contractor', css_class='col-md-4'), Column('consultant', css_class='col-md-4')),
                'location',
            ),
            Fieldset('Schedule & Finance',
                Row(Column('start_date', css_class='col-md-4'), Column('finish_date', css_class='col-md-4'), Column('status', css_class='col-md-4')),
                'contract_value',
            ),
            'description',
            Submit('submit', 'Save Project', css_class='btn btn-primary'),
        )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        finish = cleaned_data.get('finish_date')
        if start and finish and finish <= start:
            raise forms.ValidationError('Finish date must be after start date.')
        return cleaned_data


class StakeholderForm(forms.ModelForm):
    class Meta:
        model = Stakeholder
        fields = ['name', 'company', 'role', 'email', 'phone', 'is_primary']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-6'), Column('company', css_class='col-md-6')),
            Row(Column('role', css_class='col-md-4'), Column('email', css_class='col-md-4'), Column('phone', css_class='col-md-4')),
            'is_primary',
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )


class WorkAreaForm(forms.ModelForm):
    class Meta:
        model = WorkArea
        fields = ['name', 'description', 'area_sqm']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-6'), Column('area_sqm', css_class='col-md-6')),
            'description',
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )
