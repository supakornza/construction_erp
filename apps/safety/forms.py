from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import ToolboxMeeting, SafetyInspection, IncidentReport, JSEARecord


class ToolboxMeetingForm(forms.ModelForm):
    class Meta:
        model = ToolboxMeeting
        fields = ['project', 'meeting_date', 'topic', 'location', 'conducted_by', 'attendee_count', 'attachment', 'remarks']
        widgets = {
            'meeting_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('meeting_date', css_class='col-md-6')),
            'topic',
            Row(Column('location', css_class='col-md-6'), Column('conducted_by', css_class='col-md-6')),
            Row(Column('attendee_count', css_class='col-md-4'), Column('attachment', css_class='col-md-8')),
            'remarks',
            Submit('submit', 'Save Meeting', css_class='btn btn-primary'),
        )


class SafetyInspectionForm(forms.ModelForm):
    class Meta:
        model = SafetyInspection
        fields = ['project', 'inspection_date', 'location', 'inspector', 'category',
                  'finding', 'action_required', 'responsible_person', 'due_date', 'status', 'close_date', 'attachment']
        widgets = {
            'inspection_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'due_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'close_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'finding': forms.Textarea(attrs={'rows': 3}),
            'action_required': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('inspection_date', css_class='col-md-6')),
            Row(Column('location', css_class='col-md-6'), Column('inspector', css_class='col-md-6')),
            Row(Column('category', css_class='col-md-6'), Column('responsible_person', css_class='col-md-6')),
            'finding', 'action_required',
            Row(Column('due_date', css_class='col-md-4'), Column('status', css_class='col-md-4'), Column('close_date', css_class='col-md-4')),
            'attachment',
            Submit('submit', 'Save Inspection', css_class='btn btn-primary'),
        )


class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = ['project', 'incident_date', 'incident_time', 'location', 'type',
                  'description', 'injured_person', 'root_cause', 'corrective_action', 'reported_by', 'status']
        widgets = {
            'incident_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'incident_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'root_cause': forms.Textarea(attrs={'rows': 2}),
            'corrective_action': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('incident_date', css_class='col-md-3'), Column('incident_time', css_class='col-md-3')),
            Row(Column('location', css_class='col-md-6'), Column('type', css_class='col-md-6')),
            'description',
            Row(Column('injured_person', css_class='col-md-6'), Column('reported_by', css_class='col-md-6')),
            'root_cause', 'corrective_action',
            Row(Column('status', css_class='col-md-4')),
            Submit('submit', 'Save Incident Report', css_class='btn btn-primary'),
        )


class JSEARecordForm(forms.ModelForm):
    class Meta:
        model = JSEARecord
        fields = ['project', 'work_activity', 'date', 'work_area', 'prepared_by', 'approved_by', 'attachment']
        widgets = {'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('date', css_class='col-md-6')),
            'work_activity',
            Row(Column('work_area', css_class='col-md-12')),
            Row(Column('prepared_by', css_class='col-md-6'), Column('approved_by', css_class='col-md-6')),
            'attachment',
            Submit('submit', 'Save JSEA', css_class='btn btn-primary'),
        )
