from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Drawing, RFI


class DrawingForm(forms.ModelForm):
    class Meta:
        model  = Drawing
        fields = [
            'project', 'drawing_no', 'title', 'discipline', 'revision',
            'status', 'issue_date', 'prepared_by', 'description', 'file',
        ]
        widgets = {
            'issue_date':  forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'),
                Column('discipline', css_class='col-md-6')),
            Row(Column('drawing_no', css_class='col-md-6'),
                Column('title', css_class='col-md-6')),
            Row(Column('revision', css_class='col-md-3'),
                Column('status', css_class='col-md-3'),
                Column('issue_date', css_class='col-md-3'),
                Column('prepared_by', css_class='col-md-3')),
            'description',
            'file',
            Submit('submit', 'Save Drawing', css_class='btn btn-primary'),
        )


class DrawingRevisionForm(forms.ModelForm):
    class Meta:
        model  = Drawing
        fields = ['revision', 'status', 'issue_date', 'prepared_by', 'description', 'file']
        widgets = {
            'issue_date':  forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('revision', css_class='col-md-3'),
                Column('status', css_class='col-md-4'),
                Column('issue_date', css_class='col-md-3'),
                Column('prepared_by', css_class='col-md-2')),
            'description',
            'file',
            Submit('submit', 'Issue New Revision', css_class='btn btn-primary'),
        )


class RFIForm(forms.ModelForm):
    class Meta:
        model  = RFI
        fields = [
            'project', 'subject', 'description', 'drawing',
            'priority', 'submitted_by', 'submitted_date',
            'response_required_date', 'attachment',
        ]
        widgets = {
            'submitted_date':         forms.DateInput(attrs={'type': 'date'}),
            'response_required_date': forms.DateInput(attrs={'type': 'date'}),
            'description':            forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'),
                Column('priority', css_class='col-md-6')),
            'subject',
            'description',
            'drawing',
            Row(Column('submitted_by', css_class='col-md-4'),
                Column('submitted_date', css_class='col-md-4'),
                Column('response_required_date', css_class='col-md-4')),
            'attachment',
            Submit('submit', 'Save RFI', css_class='btn btn-primary'),
        )


class RFIAnswerForm(forms.ModelForm):
    class Meta:
        model  = RFI
        fields = ['answer', 'answered_date']
        widgets = {
            'answer':       forms.Textarea(attrs={'rows': 5}),
            'answered_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'answer',
            'answered_date',
            Submit('submit', 'Submit Answer', css_class='btn btn-success'),
        )
