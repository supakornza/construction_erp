from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset
from .models import DailyReport, DailyWorkActivity, DailyLookahead, DailyProblemRemark, DailyPhoto


class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = ['project', 'report_date', 'weather_morning', 'weather_afternoon',
                  'prepared_by', 'checked_by', 'remarks']
        widgets = {
            'report_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # prevent nested <form> inside outer form
        self.helper.layout = Layout(
            Fieldset('Report Details',
                Row(Column('project', css_class='col-md-6'), Column('report_date', css_class='col-md-6')),
                Row(Column('weather_morning', css_class='col-md-6'), Column('weather_afternoon', css_class='col-md-6')),
            ),
            Fieldset('Personnel',
                Row(Column('prepared_by', css_class='col-md-6'), Column('checked_by', css_class='col-md-6')),
            ),
            'remarks',
        )


class RejectionForm(forms.Form):
    rejection_reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Rejection Reason')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'rejection_reason',
            Submit('submit', 'Reject Report', css_class='btn btn-danger'),
        )


DailyWorkActivityFormSet = inlineformset_factory(
    DailyReport, DailyWorkActivity,
    fields=['work_area', 'description', 'quantity', 'unit', 'percent_complete', 'remarks'],
    extra=2, can_delete=True
)

DailyLookaheadFormSet = inlineformset_factory(
    DailyReport, DailyLookahead,
    fields=['planned_activity', 'planned_date', 'responsible_person'],
    widgets={'planned_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})},
    extra=2, can_delete=True
)

DailyProblemFormSet = inlineformset_factory(
    DailyReport, DailyProblemRemark,
    fields=['category', 'description', 'impact', 'corrective_action', 'status'],
    extra=1, can_delete=True
)

DailyPhotoFormSet = inlineformset_factory(
    DailyReport, DailyPhoto,
    fields=['caption', 'photo', 'location', 'taken_at'],
    widgets={'taken_at': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'})},
    extra=1, can_delete=True
)
