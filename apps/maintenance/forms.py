from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import MaintenanceSchedule, MaintenanceWorkOrder, MaintenancePart


class MaintenanceScheduleForm(forms.ModelForm):
    class Meta:
        model  = MaintenanceSchedule
        fields = [
            'equipment', 'title', 'work_type', 'description',
            'interval_type', 'interval_value',
            'last_done_date', 'last_done_hours',
            'next_due_date', 'next_due_hours',
            'is_active',
        ]
        widgets = {
            'last_done_date': forms.DateInput(attrs={'type': 'date'}),
            'next_due_date':  forms.DateInput(attrs={'type': 'date'}),
            'description':    forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('equipment', css_class='col-md-8'),
                Column('is_active', css_class='col-md-4 d-flex align-items-end pb-2')),
            'title',
            Row(Column('work_type', css_class='col-md-6'),
                Column('interval_type', css_class='col-md-3'),
                Column('interval_value', css_class='col-md-3')),
            'description',
            Row(Column('last_done_date', css_class='col-md-3'),
                Column('last_done_hours', css_class='col-md-3'),
                Column('next_due_date', css_class='col-md-3'),
                Column('next_due_hours', css_class='col-md-3')),
            Submit('submit', 'Save Schedule', css_class='btn btn-primary'),
        )


class MaintenanceWorkOrderForm(forms.ModelForm):
    class Meta:
        model  = MaintenanceWorkOrder
        fields = [
            'equipment', 'schedule', 'project', 'title', 'work_type', 'priority',
            'planned_date', 'description', 'assigned_to',
        ]
        widgets = {
            'planned_date': forms.DateInput(attrs={'type': 'date'}),
            'description':  forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('equipment', css_class='col-md-6'),
                Column('project', css_class='col-md-6')),
            'schedule',
            'title',
            Row(Column('work_type', css_class='col-md-4'),
                Column('priority', css_class='col-md-4'),
                Column('planned_date', css_class='col-md-4')),
            'description',
            'assigned_to',
            Submit('submit', 'Save Work Order', css_class='btn btn-primary'),
        )


class WorkOrderCompleteForm(forms.ModelForm):
    class Meta:
        model  = MaintenanceWorkOrder
        fields = [
            'actual_start', 'actual_end', 'running_hours_at_service',
            'findings', 'actions_taken', 'cost',
            'next_service_due_date', 'next_service_due_hours',
        ]
        widgets = {
            'actual_start':           forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'actual_end':             forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'next_service_due_date':  forms.DateInput(attrs={'type': 'date'}),
            'findings':               forms.Textarea(attrs={'rows': 3}),
            'actions_taken':          forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('actual_start', css_class='col-md-4'),
                Column('actual_end', css_class='col-md-4'),
                Column('running_hours_at_service', css_class='col-md-4')),
            'findings',
            'actions_taken',
            Row(Column('cost', css_class='col-md-4'),
                Column('next_service_due_date', css_class='col-md-4'),
                Column('next_service_due_hours', css_class='col-md-4')),
            Submit('submit', 'Mark as Completed', css_class='btn btn-success'),
        )


class MaintenancePartForm(forms.ModelForm):
    class Meta:
        model  = MaintenancePart
        fields = ['part_name', 'part_no', 'quantity', 'unit', 'unit_cost']
        widgets = {
            'part_name': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'part_no':   forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'quantity':  forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'unit':      forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
        }


MaintenancePartFormSet = inlineformset_factory(
    MaintenanceWorkOrder, MaintenancePart,
    form=MaintenancePartForm,
    extra=1, can_delete=True,
)
