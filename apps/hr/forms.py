from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import Employee, AttendanceRecord, LeaveRequest, OvertimeRequest


class EmployeeForm(forms.ModelForm):
    class Meta:
        model  = Employee
        fields = [
            'user', 'first_name', 'last_name', 'nickname',
            'id_card_no', 'nationality', 'date_of_birth', 'phone', 'email',
            'company', 'position', 'category', 'employment_type',
            'project', 'start_date', 'end_date', 'status', 'photo', 'remarks',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'start_date':    forms.DateInput(attrs={'type': 'date'}),
            'end_date':      forms.DateInput(attrs={'type': 'date'}),
            'remarks':       forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-4'),
                Column('last_name',  css_class='col-md-4'),
                Column('nickname',   css_class='col-md-4')),
            Row(Column('id_card_no',  css_class='col-md-6'),
                Column('nationality', css_class='col-md-3'),
                Column('date_of_birth', css_class='col-md-3')),
            Row(Column('phone', css_class='col-md-6'), Column('email', css_class='col-md-6')),
            Row(Column('company',    css_class='col-md-6'),
                Column('position',   css_class='col-md-6')),
            Row(Column('category',        css_class='col-md-4'),
                Column('employment_type', css_class='col-md-4'),
                Column('status',          css_class='col-md-4')),
            Row(Column('project',    css_class='col-md-4'),
                Column('start_date', css_class='col-md-4'),
                Column('end_date',   css_class='col-md-4')),
            'user', 'photo', 'remarks',
            Submit('submit', 'Save Employee', css_class='btn btn-primary'),
        )


class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model  = AttendanceRecord
        fields = ['employee', 'project', 'record_date', 'status',
                  'time_in', 'time_out', 'overtime_hours', 'remarks']
        widgets = {
            'record_date': forms.DateInput(attrs={'type': 'date'}),
            'time_in':     forms.TimeInput(attrs={'type': 'time'}),
            'time_out':    forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('employee', css_class='col-md-6'), Column('project', css_class='col-md-6')),
            Row(Column('record_date', css_class='col-md-4'), Column('status', css_class='col-md-4')),
            Row(Column('time_in', css_class='col-md-3'), Column('time_out', css_class='col-md-3'),
                Column('overtime_hours', css_class='col-md-3')),
            'remarks',
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )


class BulkAttendanceForm(forms.Form):
    project     = forms.ModelChoiceField(queryset=None, required=False)
    record_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        from apps.projects.models import Project
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.filter(status='Active')


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model  = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
            'reason':     forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'employee',
            Row(Column('leave_type', css_class='col-md-4'),
                Column('start_date', css_class='col-md-4'),
                Column('end_date',   css_class='col-md-4')),
            'reason',
            Submit('submit', 'Submit Leave Request', css_class='btn btn-primary'),
        )


class OvertimeRequestForm(forms.ModelForm):
    class Meta:
        model  = OvertimeRequest
        fields = ['employee', 'project', 'ot_date', 'planned_hours', 'reason']
        widgets = {
            'ot_date': forms.DateInput(attrs={'type': 'date'}),
            'reason':  forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('employee', css_class='col-md-6'), Column('project', css_class='col-md-6')),
            Row(Column('ot_date', css_class='col-md-4'), Column('planned_hours', css_class='col-md-4')),
            'reason',
            Submit('submit', 'Request OT Approval', css_class='btn btn-warning'),
        )


class LeaveDecisionForm(forms.Form):
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label='Reason (required for rejection)',
    )


class OTActualHoursForm(forms.Form):
    actual_hours = forms.DecimalField(max_digits=4, decimal_places=2,
                                      label='Actual OT Hours Worked')
