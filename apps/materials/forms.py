from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Material, MaterialDelivery, MaterialUsage


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name', 'category', 'unit', 'unit_weight', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-6'), Column('category', css_class='col-md-6')),
            Row(Column('unit', css_class='col-md-6'), Column('unit_weight', css_class='col-md-6')),
            'description',
            Submit('submit', 'Save', css_class='btn btn-primary'),
        )


class MaterialDeliveryForm(forms.ModelForm):
    class Meta:
        model = MaterialDelivery
        fields = ['project', 'delivery_date', 'material', 'source', 'truck_no',
                  'delivery_note_no', 'quantity', 'unit_price', 'remarks']
        widgets = {'delivery_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('delivery_date', css_class='col-md-6')),
            Row(Column('material', css_class='col-md-6'), Column('quantity', css_class='col-md-3'), Column('unit_price', css_class='col-md-3')),
            Row(Column('delivery_note_no', css_class='col-md-4'), Column('truck_no', css_class='col-md-4'), Column('source', css_class='col-md-4')),
            'remarks',
            Submit('submit', 'Record Delivery', css_class='btn btn-primary'),
        )


class MaterialUsageForm(forms.ModelForm):
    class Meta:
        model = MaterialUsage
        fields = ['project', 'usage_date', 'material', 'work_area', 'quantity', 'remarks']
        widgets = {'usage_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('usage_date', css_class='col-md-6')),
            Row(Column('material', css_class='col-md-4'), Column('work_area', css_class='col-md-4'), Column('quantity', css_class='col-md-4')),
            'remarks',
            Submit('submit', 'Record Usage', css_class='btn btn-primary'),
        )
