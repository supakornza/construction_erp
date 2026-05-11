from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit

from .models import InspectionRequest, NonConformance, PunchList, QualityCheckpoint


class InspectionRequestForm(forms.ModelForm):
    class Meta:
        model = InspectionRequest
        fields = [
            'project', 'boq_item', 'work_package', 'inspection_date', 'location',
            'station_or_chainage', 'inspection_type', 'description', 'requested_by',
            'inspected_by', 'status', 'result', 'remarks',
        ]
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('boq_item', css_class='col-md-6')),
            Row(Column('inspection_date', css_class='col-md-4'), Column('inspection_type', css_class='col-md-4'), Column('work_package', css_class='col-md-4')),
            Row(Column('location', css_class='col-md-6'), Column('station_or_chainage', css_class='col-md-6')),
            'description',
            Row(Column('requested_by', css_class='col-md-6'), Column('inspected_by', css_class='col-md-6')),
            Row(Column('status', css_class='col-md-6'), Column('result', css_class='col-md-6')),
            'remarks',
            Submit('submit', 'Save Inspection Request', css_class='btn btn-primary'),
        )


class QualityCheckpointForm(forms.ModelForm):
    class Meta:
        model = QualityCheckpoint
        fields = ['project', 'boq_item', 'checkpoint_name', 'specification_ref', 'acceptance_criteria', 'frequency', 'is_active']
        widgets = {'acceptance_criteria': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('boq_item', css_class='col-md-6')),
            Row(Column('checkpoint_name', css_class='col-md-6'), Column('specification_ref', css_class='col-md-6')),
            'acceptance_criteria',
            Row(Column('frequency', css_class='col-md-6'), Column('is_active', css_class='col-md-6')),
            Submit('submit', 'Save Checkpoint', css_class='btn btn-primary'),
        )


class NonConformanceForm(forms.ModelForm):
    class Meta:
        model = NonConformance
        fields = [
            'project', 'inspection_request', 'boq_item', 'ncr_no', 'description',
            'root_cause', 'corrective_action', 'preventive_action',
            'responsible_person', 'issued_date', 'due_date', 'closed_date',
            'status', 'severity', 'attachment',
        ]
        widgets = {
            'issued_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'closed_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'root_cause': forms.Textarea(attrs={'rows': 2}),
            'corrective_action': forms.Textarea(attrs={'rows': 2}),
            'preventive_action': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {'enctype': 'multipart/form-data'}
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-4'), Column('ncr_no', css_class='col-md-4'), Column('severity', css_class='col-md-4')),
            Row(Column('inspection_request', css_class='col-md-6'), Column('boq_item', css_class='col-md-6')),
            'description',
            'root_cause',
            Row(Column('corrective_action', css_class='col-md-6'), Column('preventive_action', css_class='col-md-6')),
            Row(Column('responsible_person', css_class='col-md-6'), Column('status', css_class='col-md-6')),
            Row(Column('issued_date', css_class='col-md-4'), Column('due_date', css_class='col-md-4'), Column('closed_date', css_class='col-md-4')),
            'attachment',
            Submit('submit', 'Save NCR', css_class='btn btn-primary'),
        )


class PunchListForm(forms.ModelForm):
    class Meta:
        model = PunchList
        fields = ['project', 'description', 'location', 'responsible_person', 'target_date', 'closed_date', 'status', 'priority', 'attachment']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'closed_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {'enctype': 'multipart/form-data'}
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('location', css_class='col-md-6')),
            'description',
            Row(Column('responsible_person', css_class='col-md-4'), Column('priority', css_class='col-md-4'), Column('status', css_class='col-md-4')),
            Row(Column('target_date', css_class='col-md-6'), Column('closed_date', css_class='col-md-6')),
            'attachment',
            Submit('submit', 'Save Punch List Item', css_class='btn btn-primary'),
        )
