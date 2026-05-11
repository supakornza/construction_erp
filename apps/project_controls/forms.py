from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset
from .models import (
    RockDailyRecord, RockBargePlacement,
    SandDailyRecord, SandBargePlacement,
    SandAllocation, RecoveryPlan, RecoveryPlanDailyItem,
    RecoveryActionPlan, RecoveryActionItem,
    RecoveryActionDailyProgress, LogisticsScenario,
    RevetmentStation, RevetmentActivity,
    RevetmentDailyRecord, RevetmentDailyItem,
)


class RockDailyRecordForm(forms.ModelForm):
    class Meta:
        model = RockDailyRecord
        fields = ['project', 'record_date', 'day_name',
                  'tct_daily_ton', 'tct_trips', 'tct_trucks',
                  'placed_daily_ton', 'station_of_core',
                  'core_outside_daily', 'core_inside_accum', 'remarks']
        widgets = {
            'record_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
            'station_of_core': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset('Record Details',
                Row(Column('project', css_class='col-md-4'),
                    Column('record_date', css_class='col-md-4'),
                    Column('day_name', css_class='col-md-4')),
            ),
            Fieldset('Rock at TCT Port (Weight Bridge)',
                Row(Column('tct_daily_ton', css_class='col-md-4'),
                    Column('tct_trips', css_class='col-md-4'),
                    Column('tct_trucks', css_class='col-md-4')),
            ),
            Fieldset('Rock Placement',
                Row(Column('placed_daily_ton', css_class='col-md-6'),
                    Column('station_of_core', css_class='col-md-6')),
            ),
            Fieldset('Core Quantities',
                Row(Column('core_outside_daily', css_class='col-md-6'),
                    Column('core_inside_accum', css_class='col-md-6')),
            ),
            'remarks',
        )


RockBargePlacementFormSet = inlineformset_factory(
    RockDailyRecord, RockBargePlacement,
    fields=['barge', 'quantity_ton', 'trips', 'station', 'remarks'],
    extra=4, can_delete=True,
)


class SandDailyRecordForm(forms.ModelForm):
    sand_source = forms.ChoiceField(required=False, label='Sand source')

    class Meta:
        model = SandDailyRecord
        fields = [
            'project', 'record_date', 'day_name',
            'tct_daily_ton', 'tct_trips', 'tct_trucks',
            'mtp3_daily_ton', 'mtp3_trips', 'mtp3_trucks',
            'sand_source', 'oswald_daily_ton', 'oswald_trips', 'oswald_trucks',
            'offshore_daily_ton', 'offshore_station',
            'onshore_daily_ton', 'onshore_trips', 'onshore_trucks',
            'inside_plot_daily', 'outside_plot_daily',
            'remaining_tct', 'remaining_mtp3',
            'remarks',
        ]
        widgets = {
            'record_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.materials.models import MaterialDelivery

        sources = (
            MaterialDelivery.objects
            .filter(material__name__icontains='Sand')
            .exclude(source='')
            .values_list('source', flat=True)
            .distinct()
            .order_by('source')
        )
        source_values = list(sources)
        current_source = self.initial.get('sand_source') or getattr(self.instance, 'sand_source', '') or ''
        for value in ['Oswald', current_source]:
            if value and value not in source_values:
                source_values.append(value)
        self.fields['sand_source'].choices = [('', '---------')] + [(source, source) for source in source_values]
        self.fields['oswald_daily_ton'].label = 'Other source daily ton'
        self.fields['oswald_trips'].label = 'Other source trips'
        self.fields['oswald_trucks'].label = 'Other source trucks'
        self.helper = FormHelper()
        self.helper.form_tag = False


SandBargePlacementFormSet = inlineformset_factory(
    SandDailyRecord, SandBargePlacement,
    fields=['barge', 'quantity_ton', 'trips', 'station'],
    extra=4, can_delete=True,
)


class SandAllocationForm(forms.ModelForm):
    class Meta:
        model = SandAllocation
        fields = ['project', 'calculation_date', 'total_sand_quantity',
                  'tct_percentage', 'mtp3_percentage', 'total_trips', 'remarks']
        widgets = {
            'calculation_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class RevetmentStationForm(forms.ModelForm):
    class Meta:
        model = RevetmentStation
        fields = ['project', 'sop', 'station', 'sort_order', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class RevetmentActivityForm(forms.ModelForm):
    class Meta:
        model = RevetmentActivity
        fields = ['project', 'group_name', 'name', 'template_column', 'unit',
                  'is_inspection', 'sort_order', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class RevetmentDailyRecordForm(forms.ModelForm):
    class Meta:
        model = RevetmentDailyRecord
        fields = ['project', 'record_date', 'day_name', 'remarks']
        widgets = {
            'record_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class RevetmentDailyItemForm(forms.ModelForm):
    class Meta:
        model = RevetmentDailyItem
        fields = ['station', 'activity', 'quantity_done', 'status', 'inspection_date', 'remarks']
        widgets = {
            'quantity_done': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.TextInput(),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        station_qs = RevetmentStation.objects.filter(is_active=True)
        activity_qs = RevetmentActivity.objects.filter(is_active=True)
        if project:
            station_qs = station_qs.filter(project=project)
            activity_qs = activity_qs.filter(project=project)
        self.fields['station'].queryset = station_qs
        self.fields['activity'].queryset = activity_qs
        self.fields['quantity_done'].required = False
        self.fields['status'].required = False
        self.fields['inspection_date'].required = False


RevetmentDailyItemFormSet = inlineformset_factory(
    RevetmentDailyRecord, RevetmentDailyItem,
    form=RevetmentDailyItemForm,
    extra=6, can_delete=True,
)


class RecoveryPlanForm(forms.ModelForm):
    class Meta:
        model = RecoveryPlan
        fields = ['project', 'plan_name', 'material_type', 'start_date', 'end_date',
                  'description', 'status', 'prepared_by', 'approved_by']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class RecoveryActionPlanForm(forms.ModelForm):
    class Meta:
        model = RecoveryActionPlan
        fields = ['project', 'title', 'start_date', 'end_date', 'status',
                  'prepared_by', 'approved_by', 'remarks']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


RecoveryPlanDailyItemFormSet = inlineformset_factory(
    RecoveryPlan, RecoveryPlanDailyItem,
    fields=['plan_date', 'day_name', 'planned_quantity', 'actual_quantity'],
    extra=14, can_delete=True,
    widgets={
        'plan_date': forms.DateInput(attrs={'type': 'date'}),
        'planned_quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        'actual_quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
    },
)

RecoveryActionItemFormSet = inlineformset_factory(
    RecoveryActionPlan, RecoveryActionItem,
    fields=['item_no', 'description', 'total_quantity', 'unit', 'ntp_reference', 'remarks'],
    extra=3, can_delete=True,
)


class RecoveryActionDailyProgressForm(forms.ModelForm):
    class Meta:
        model = RecoveryActionDailyProgress
        fields = ['progress_date', 'planned_quantity', 'actual_quantity', 'remarks']
        widgets = {
            'progress_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }


class LogisticsScenarioForm(forms.ModelForm):
    class Meta:
        model = LogisticsScenario
        fields = [
            'project', 'scenario_name', 'material_type',
            'number_of_trucks', 'truck_capacity_ton',
            'route_distance_km', 'average_speed_kmph',
            'loading_time_min', 'unloading_time_min',
            'allowed_start_time_1', 'allowed_end_time_1',
            'allowed_start_time_2', 'allowed_end_time_2',
            'working_hours', 'remarks',
        ]
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
            'allowed_start_time_1': forms.TimeInput(attrs={'type': 'time'}),
            'allowed_end_time_1': forms.TimeInput(attrs={'type': 'time'}),
            'allowed_start_time_2': forms.TimeInput(attrs={'type': 'time'}),
            'allowed_end_time_2': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class ImportForm(forms.Form):
    IMPORT_TYPE_CHOICES = [
        ('rock_summary', 'Rock Summary'),
        ('sand_summary', 'Sand Summary'),
        ('recovery_action_plan', 'Recovery Action Plan'),
        ('revetment_progress', 'Revetment Progress'),
    ]
    project = forms.ModelChoiceField(queryset=None)
    import_type = forms.ChoiceField(choices=IMPORT_TYPE_CHOICES)
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload .xlsx file matching the required template',
    )
    duplicate_action = forms.ChoiceField(
        choices=[('update', 'Update existing'), ('skip', 'Skip duplicates')],
        initial='update',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.projects.models import Project
        self.fields['project'].queryset = Project.objects.filter(status='Active')
        self.helper = FormHelper()
        self.helper.form_tag = False
