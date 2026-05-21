from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import ChangeOrder, ChangeOrderItem


class ChangeOrderForm(forms.ModelForm):
    class Meta:
        model  = ChangeOrder
        fields = [
            'project', 'title', 'description', 'type', 'initiated_by',
            'contract_value_impact', 'time_impact_days',
            'initiated_date', 'attachment',
        ]
        widgets = {
            'initiated_date': forms.DateInput(attrs={'type': 'date'}),
            'description':    forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('initiated_date', css_class='col-md-6')),
            'title',
            Row(Column('type', css_class='col-md-6'), Column('initiated_by', css_class='col-md-6')),
            'description',
            Row(
                Column('contract_value_impact', css_class='col-md-6'),
                Column('time_impact_days', css_class='col-md-6'),
            ),
            'attachment',
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )


class ChangeOrderItemForm(forms.ModelForm):
    class Meta:
        model  = ChangeOrderItem
        fields = [
            'boq_item', 'description', 'unit', 'change_type',
            'original_quantity', 'revised_quantity', 'unit_rate', 'remarks',
        ]
        widgets = {
            'description':       forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'unit':              forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'change_type':       forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'original_quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.001'}),
            'revised_quantity':  forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.001'}),
            'unit_rate':         forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'remarks':           forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'boq_item':          forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }


ChangeOrderItemFormSet = inlineformset_factory(
    ChangeOrder, ChangeOrderItem,
    form=ChangeOrderItemForm,
    extra=1,
    can_delete=True,
)


class RejectionForm(forms.Form):
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Reason for Rejection',
    )
