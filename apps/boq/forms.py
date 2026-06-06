from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import BOQItem, DailyProgressRecord, PaymentClaim


class BOQItemForm(forms.ModelForm):
    class Meta:
        model = BOQItem
        fields = ['project', 'item_no', 'item_type', 'description', 'contract_quantity', 'unit', 'unit_rate']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('item_no', css_class='col-md-3'), Column('item_type', css_class='col-md-3')),
            'description',
            Row(Column('contract_quantity', css_class='col-md-4'), Column('unit', css_class='col-md-4'), Column('unit_rate', css_class='col-md-4'), css_id='qty-row'),
            Submit('submit', 'Save BOQ Item', css_class='btn btn-primary'),
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.parent = BOQItem.find_parent(instance.project, instance.item_no, exclude_pk=instance.pk)
        if commit:
            instance.save()
        return instance


class DailyProgressRecordForm(forms.ModelForm):
    class Meta:
        model = DailyProgressRecord
        fields = ['project', 'boq_item', 'record_date', 'daily_quantity', 'remarks', 'allow_overrun']
        widgets = {'record_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['boq_item'].queryset = BOQItem.objects.filter(item_type='item')
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('record_date', css_class='col-md-6')),
            Row(Column('boq_item', css_class='col-md-6'), Column('daily_quantity', css_class='col-md-6')),
            'remarks', 'allow_overrun',
            Submit('submit', 'Record Progress', css_class='btn btn-primary'),
        )


class BOQImportForm(forms.Form):
    project = forms.ModelChoiceField(queryset=None)
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a .csv file with columns: รหัส, รายการ, หน่วย, ปริมาณ, ราคาต่อหน่วย (UTF-8 or UTF-8 with BOM)',
    )
    duplicate_action = forms.ChoiceField(
        choices=[('skip', 'Skip duplicates'), ('update', 'Update existing')],
        initial='skip',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.projects.models import Project
        self.fields['project'].queryset = Project.objects.all()
        self.helper = FormHelper()
        self.helper.form_tag = False


class PaymentClaimForm(forms.ModelForm):
    class Meta:
        model = PaymentClaim
        fields = ['project', 'claim_no', 'claim_date', 'period_from', 'period_to', 'total_claimed_amount', 'status']
        widgets = {
            'claim_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'period_from': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'period_to': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('project', css_class='col-md-6'), Column('claim_no', css_class='col-md-6')),
            Row(Column('claim_date', css_class='col-md-4'), Column('period_from', css_class='col-md-4'), Column('period_to', css_class='col-md-4')),
            Row(Column('total_claimed_amount', css_class='col-md-6'), Column('status', css_class='col-md-6')),
            Submit('submit', 'Save Claim', css_class='btn btn-primary'),
        )
