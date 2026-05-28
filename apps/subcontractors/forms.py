from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Subcontractor, SubcontractorContract, SubcontractorWorkItem, PaymentClaim


class SubcontractorForm(forms.ModelForm):
    class Meta:
        model  = Subcontractor
        fields = [
            'name', 'registration_no', 'category', 'status',
            'contact_person', 'phone', 'email', 'address', 'tax_id',
            'bank_account', 'notes',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes':   forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-8'),
                Column('category', css_class='col-md-4')),
            Row(Column('registration_no', css_class='col-md-4'),
                Column('tax_id', css_class='col-md-4'),
                Column('status', css_class='col-md-4')),
            Row(Column('contact_person', css_class='col-md-4'),
                Column('phone', css_class='col-md-4'),
                Column('email', css_class='col-md-4')),
            'address',
            'bank_account',
            'notes',
            Submit('submit', 'Save Subcontractor', css_class='btn btn-primary'),
        )


class SubcontractorContractForm(forms.ModelForm):
    class Meta:
        model  = SubcontractorContract
        fields = [
            'project', 'subcontractor', 'title', 'contract_type',
            'contract_value', 'retention_pct', 'scope_of_work',
            'start_date', 'end_date', 'signed_date', 'status',
        ]
        widgets = {
            'scope_of_work': forms.Textarea(attrs={'rows': 3}),
            'start_date':    forms.DateInput(attrs={'type': 'date'}),
            'end_date':      forms.DateInput(attrs={'type': 'date'}),
            'signed_date':   forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'),
                Column('subcontractor', css_class='col-md-6')),
            'title',
            Row(Column('contract_type', css_class='col-md-4'),
                Column('contract_value', css_class='col-md-4'),
                Column('retention_pct', css_class='col-md-4')),
            'scope_of_work',
            Row(Column('start_date', css_class='col-md-3'),
                Column('end_date', css_class='col-md-3'),
                Column('signed_date', css_class='col-md-3'),
                Column('status', css_class='col-md-3')),
        )


class WorkItemForm(forms.ModelForm):
    class Meta:
        model  = SubcontractorWorkItem
        fields = ['description', 'unit', 'contract_qty', 'unit_rate', 'completed_qty']
        widgets = {
            'description':  forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'unit':         forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'contract_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.001'}),
            'unit_rate':    forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'completed_qty': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.001'}),
        }


WorkItemFormSet = inlineformset_factory(
    SubcontractorContract, SubcontractorWorkItem,
    form=WorkItemForm, extra=1, can_delete=True,
)


class PaymentClaimForm(forms.ModelForm):
    class Meta:
        model  = PaymentClaim
        fields = ['claim_date', 'period_from', 'period_to', 'claimed_amount', 'notes']
        widgets = {
            'claim_date':  forms.DateInput(attrs={'type': 'date'}),
            'period_from': forms.DateInput(attrs={'type': 'date'}),
            'period_to':   forms.DateInput(attrs={'type': 'date'}),
            'notes':       forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('claim_date', css_class='col-md-4'),
                Column('period_from', css_class='col-md-4'),
                Column('period_to', css_class='col-md-4')),
            'claimed_amount',
            'notes',
            Submit('submit', 'Save Claim', css_class='btn btn-primary'),
        )


class ClaimCertifyForm(forms.ModelForm):
    class Meta:
        model  = PaymentClaim
        fields = ['certified_amount', 'retention_deducted', 'net_payable', 'certified_date', 'notes']
        widgets = {
            'certified_date': forms.DateInput(attrs={'type': 'date'}),
            'notes':          forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('certified_amount', css_class='col-md-4'),
                Column('retention_deducted', css_class='col-md-4'),
                Column('net_payable', css_class='col-md-4')),
            'certified_date',
            'notes',
            Submit('submit', 'Certify Payment', css_class='btn btn-success'),
        )


class ClaimPayForm(forms.ModelForm):
    class Meta:
        model  = PaymentClaim
        fields = ['paid_date', 'notes']
        widgets = {
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
            'notes':     forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'paid_date',
            'notes',
            Submit('submit', 'Mark as Paid', css_class='btn btn-success'),
        )
