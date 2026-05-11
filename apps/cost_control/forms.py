from django import forms
from .models import CostCode, BudgetItem, ActualCost


class CostCodeForm(forms.ModelForm):
    class Meta:
        model = CostCode
        fields = ['project', 'code', 'name', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class BudgetItemForm(forms.ModelForm):
    class Meta:
        model = BudgetItem
        fields = ['project', 'cost_code', 'boq_item', 'description',
                  'budget_amount', 'committed_amount', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }


class ActualCostForm(forms.ModelForm):
    class Meta:
        model = ActualCost
        fields = ['project', 'cost_code', 'cost_date', 'description',
                  'amount', 'source_type', 'reference_no', 'remarks']
        widgets = {
            'cost_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
