from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Supplier, PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'tax_id']
        widgets = {'address': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-6'), Column('tax_id', css_class='col-md-6')),
            Row(Column('contact_person', css_class='col-md-4'), Column('phone', css_class='col-md-4'), Column('email', css_class='col-md-4')),
            'address',
            Submit('submit', 'Save Supplier', css_class='btn btn-primary'),
        )


class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['project', 'requested_by', 'request_date', 'required_date', 'remarks']
        widgets = {
            'request_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'required_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('requested_by', css_class='col-md-6')),
            Row(Column('request_date', css_class='col-md-6'), Column('required_date', css_class='col-md-6')),
            'remarks',
            Submit('submit', 'Save PR', css_class='btn btn-primary'),
        )


PurchaseRequestItemFormSet = inlineformset_factory(
    PurchaseRequest, PurchaseRequestItem,
    fields=['material', 'quantity', 'unit', 'estimated_price', 'remarks'],
    extra=2, can_delete=True
)


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['pr', 'supplier', 'order_date', 'delivery_date', 'status']
        widgets = {
            'order_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'delivery_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('pr', css_class='col-md-6'), Column('supplier', css_class='col-md-6')),
            Row(Column('order_date', css_class='col-md-4'), Column('delivery_date', css_class='col-md-4'), Column('status', css_class='col-md-4')),
            Submit('submit', 'Save PO', css_class='btn btn-primary'),
        )


PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseOrderItem,
    fields=['material', 'quantity', 'unit_price', 'delivered_quantity'],
    extra=2, can_delete=True
)
