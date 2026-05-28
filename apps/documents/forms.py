from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import DocumentCategory, Document, DocumentRevision


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['project', 'document_no', 'title', 'category', 'revision', 'status', 'file', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('document_no', css_class='col-md-6')),
            'title',
            Row(Column('category', css_class='col-md-4'), Column('revision', css_class='col-md-4'), Column('status', css_class='col-md-4')),
            'file', 'description',
            Submit('submit', 'Upload Document', css_class='btn btn-primary'),
        )


class DocumentRevisionForm(forms.ModelForm):
    class Meta:
        model = DocumentRevision
        fields = ['revision_no', 'change_description', 'file']
        widgets = {'change_description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'revision_no', 'change_description', 'file',
            Submit('submit', 'Add Revision', css_class='btn btn-primary'),
        )
