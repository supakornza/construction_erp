from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset
from .models import (
    RockDailyRecord, RockBargePlacement, RockDashboardSettings, RockStationProgress,
    SandDailyRecord, SandBargePlacement, SandDashboardSettings, SandAreaProgress,
    SandAllocation, RecoveryPlan, RecoveryPlanDailyItem,
    RecoveryActionPlan, RecoveryActionItem,
    RecoveryActionDailyProgress, ProjectActionPlan, LogisticsScenario,
    RevetmentStation, RevetmentActivity,
    RevetmentDailyRecord, RevetmentDailyItem,
)


class RockDailyRecordForm(forms.ModelForm):
    class Meta:
        model = RockDailyRecord
        fields = ['project', 'record_date', 'day_name',
                  'material_type', 'source_quarry', 'destination_area',
                  'tct_daily_ton', 'tct_trips', 'tct_trucks',
                  'placed_daily_ton', 'station_of_core',
                  'core_outside_daily', 'core_inside_accum', 'remarks']
        widgets = {
            'record_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'day_name': forms.TextInput(attrs={'readonly': 'readonly'}),
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
                Row(Column('material_type', css_class='col-md-4'),
                    Column('source_quarry', css_class='col-md-4'),
                    Column('destination_area', css_class='col-md-4')),
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


class RockDashboardSettingsForm(forms.ModelForm):
    class Meta:
        model = RockDashboardSettings
        fields = ['project', 'target_quantity_ton', 'daily_target_placement_ton',
                  'planned_start_date', 'planned_finish_date', 'remarks']
        widgets = {
            'planned_start_date': forms.DateInput(attrs={'type': 'date'}),
            'planned_finish_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }


class RockStationProgressForm(forms.ModelForm):
    class Meta:
        model = RockStationProgress
        fields = ['project', 'station_range', 'material_type', 'delivered_quantity_ton',
                  'placed_quantity_ton', 'target_quantity_ton', 'remarks']


class SandDailyRecordForm(forms.ModelForm):
    class Meta:
        model = SandDailyRecord
        fields = [
            'project', 'record_date', 'day_name',
            'tct_daily_ton', 'tct_trips', 'tct_trucks',
            'mtp3_daily_ton', 'mtp3_trips', 'mtp3_trucks',
            'chalothon_daily_ton', 'chalothon_trips', 'chalothon_trucks',
            'khlong_bang_phai_daily_ton', 'khlong_bang_phai_trips', 'khlong_bang_phai_trucks',
            'offshore_daily_ton', 'offshore_station',
            'onshore_daily_ton', 'onshore_trips', 'onshore_trucks',
            'inside_plot_daily', 'outside_plot_daily',
            'remaining_tct', 'remaining_mtp3',
            'remarks',
        ]
        widgets = {
            'record_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'day_name': forms.TextInput(attrs={'readonly': 'readonly'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
            'offshore_daily_ton': forms.NumberInput(attrs={'readonly': 'readonly', 'style': 'background:#f8f9fa;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tct_daily_ton'].label = 'TCT Pier daily ton'
        self.fields['tct_trips'].label = 'TCT Pier trips'
        self.fields['tct_trucks'].label = 'TCT Pier trucks'
        self.fields['mtp3_daily_ton'].label = 'Stockpile Sand MTP3 daily ton'
        self.fields['mtp3_trips'].label = 'Stockpile Sand MTP3 trips'
        self.fields['mtp3_trucks'].label = 'Stockpile Sand MTP3 trucks'
        self.fields['chalothon_daily_ton'].label = 'Chalothon Sand Pit daily ton'
        self.fields['chalothon_trips'].label = 'Chalothon Sand Pit trips'
        self.fields['chalothon_trucks'].label = 'Chalothon Sand Pit trucks'
        self.fields['khlong_bang_phai_daily_ton'].label = 'Khlong Bang Phai / Oswald daily ton'
        self.fields['khlong_bang_phai_trips'].label = 'Khlong Bang Phai / Oswald trips'
        self.fields['khlong_bang_phai_trucks'].label = 'Khlong Bang Phai / Oswald trucks'
        self.helper = FormHelper()
        self.helper.form_tag = False


class _SandBargePlacementBaseFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        # New extra rows: barge is optional (user may leave rows blank)
        if index is not None and index >= self.initial_form_count():
            form.fields['barge'].required = False

    def save_new_objects(self, commit=True):
        self.new_objects = []
        for form in self.extra_forms:
            if not form.has_changed():
                continue
            if self.can_delete and self._should_delete_form(form):
                continue
            # Skip extra rows where barge was not selected
            if not form.cleaned_data.get('barge'):
                continue
            self.new_objects.append(self.save_new(form, commit=commit))
        return self.new_objects


SandBargePlacementFormSet = inlineformset_factory(
    SandDailyRecord, SandBargePlacement,
    formset=_SandBargePlacementBaseFormSet,
    fields=['barge', 'quantity_ton', 'trips', 'source', 'destination', 'placement_type', 'station'],
    extra=4, can_delete=True,
)


class SandDashboardSettingsForm(forms.ModelForm):
    class Meta:
        model = SandDashboardSettings
        fields = ['project', 'target_quantity_ton', 'daily_target_delivery_ton',
                  'daily_target_placement_ton', 'planned_start_date',
                  'planned_finish_date', 'remarks']
        widgets = {
            'planned_start_date': forms.DateInput(attrs={'type': 'date'}),
            'planned_finish_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }


class SandAreaProgressForm(forms.ModelForm):
    class Meta:
        model = SandAreaProgress
        fields = ['project', 'area_zone', 'placement_type', 'planned_quantity_ton',
                  'delivered_quantity_ton', 'placed_quantity_ton',
                  'planned_placed_to_date_ton', 'remarks']


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
        if not self.is_bound and not self.instance.pk:
            self.fields['date_raised'].initial = timezone.localdate()
        self.fields['description_th'].label = 'Description (TH)'
        self.fields['responsible_parties'].label = 'Responsible Party'
        self.fields['meeting_reference'].label = 'Meeting Reference'
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
            'record_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'day_name': forms.TextInput(attrs={'readonly': 'readonly'}),
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
        'plan_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        'day_name': forms.TextInput(attrs={'readonly': 'readonly'}),
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


class ProjectActionPlanForm(forms.ModelForm):
    class Meta:
        model = ProjectActionPlan
        fields = [
            'project', 'action_id', 'date_raised', 'description_th',
            'responsible_parties', 'due_date', 'priority', 'status',
            'category', 'meeting_reference', 'remarks',
        ]
        widgets = {
            'date_raised': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description_th': forms.Textarea(attrs={'rows': 3}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
        help_texts = {
            'action_id': 'Leave blank to auto-generate the next ACT number for this project.',
            'responsible_parties': 'Separate multiple parties with commas, e.g. PMC, ITD, PMC-TA.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


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
