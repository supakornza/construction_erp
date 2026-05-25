import os

from django import forms
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset

from apps.utils import image_to_jpeg_bytes

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


class DailyPhotoForm(forms.ModelForm):
    class Meta:
        model = DailyPhoto
        fields = ['caption', 'photo', 'location', 'taken_at']
        widgets = {
            'taken_at': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo or not isinstance(photo, UploadedFile):
            return photo

        try:
            jpeg_buf = image_to_jpeg_bytes(photo)
        except Exception as exc:
            raise forms.ValidationError('ไม่สามารถอ่านไฟล์รูปได้ กรุณาใช้ไฟล์ JPG, PNG, HEIC หรือ HEIF') from exc

        base_name = os.path.splitext(getattr(photo, 'name', 'daily-photo'))[0]
        return ContentFile(jpeg_buf.read(), name=f'{base_name}.jpg')


DailyPhotoFormSet = inlineformset_factory(
    DailyReport, DailyPhoto,
    form=DailyPhotoForm,
    extra=1, can_delete=True
)
