from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import KanbanTask


class KanbanTaskForm(forms.ModelForm):
    class Meta:
        model = KanbanTask
        fields = ['title', 'description', 'project', 'column', 'priority', 'assignee', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            Row(
                Column('project', css_class='col-md-6'),
                Column('column', css_class='col-md-6'),
            ),
            Row(
                Column('priority', css_class='col-md-6'),
                Column('due_date', css_class='col-md-6'),
            ),
            'assignee',
            'description',
            Submit('submit', 'Save Task', css_class='btn btn-primary mt-2'),
        )
