from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from apps.accounts.mixins import BOQViewMixin, FinancialWriteMixin
from .models import BOQItem, DailyProgressRecord, PaymentClaim
from .forms import BOQItemForm, DailyProgressRecordForm, PaymentClaimForm


class BOQItemListView(BOQViewMixin, ListView):
    model = BOQItem
    template_name = 'boq/list.html'
    context_object_name = 'items'

    def get_queryset(self):
        qs = super().get_queryset().select_related('project')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs.order_by('category', 'item_no')

    def get_context_data(self, **kwargs):
        from decimal import Decimal
        from itertools import groupby
        from apps.projects.models import Project
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.all()

        items = list(ctx['items'])
        grand_total = sum((item.contract_amount for item in items), Decimal('0'))

        def pct(amount):
            return (amount / grand_total * 100) if grand_total else Decimal('0')

        groups = []
        for category, group_iter in groupby(items, key=lambda i: i.category):
            group_items = list(group_iter)
            subtotal = sum((i.contract_amount for i in group_items), Decimal('0'))
            groups.append({
                'name': category or 'Uncategorized',
                'items': group_items,
                'subtotal': subtotal,
                'percent': pct(subtotal),
            })
        ctx['groups'] = groups
        ctx['grand_total'] = grand_total
        ctx['sections'] = sorted(groups, key=lambda g: g['subtotal'], reverse=True)
        ctx['top_items'] = [
            {'item': item, 'percent': pct(item.contract_amount)}
            for item in sorted(items, key=lambda i: i.contract_amount, reverse=True)[:10]
        ]
        return ctx


class BOQItemCreateView(FinancialWriteMixin, CreateView):
    model = BOQItem
    form_class = BOQItemForm
    template_name = 'boq/form.html'
    success_url = reverse_lazy('boq:list')

    def form_valid(self, form):
        messages.success(self.request, 'BOQ item created.')
        return super().form_valid(form)


class BOQItemUpdateView(FinancialWriteMixin, UpdateView):
    model = BOQItem
    form_class = BOQItemForm
    template_name = 'boq/form.html'
    success_url = reverse_lazy('boq:list')


class BOQItemDeleteView(FinancialWriteMixin, DeleteView):
    model = BOQItem
    template_name = 'boq/confirm_delete.html'
    success_url = reverse_lazy('boq:list')


class DailyProgressRecordListView(BOQViewMixin, ListView):
    model = DailyProgressRecord
    template_name = 'boq/progress_list.html'
    context_object_name = 'records'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'boq_item')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs


class DailyProgressRecordCreateView(FinancialWriteMixin, CreateView):
    model = DailyProgressRecord
    form_class = DailyProgressRecordForm
    template_name = 'boq/progress_form.html'
    success_url = reverse_lazy('boq:progress_list')

    def form_valid(self, form):
        messages.success(self.request, 'Progress recorded.')
        return super().form_valid(form)


class PaymentClaimListView(BOQViewMixin, ListView):
    model = PaymentClaim
    template_name = 'boq/claim_list.html'
    context_object_name = 'claims'
    paginate_by = 20


class PaymentClaimCreateView(FinancialWriteMixin, CreateView):
    model = PaymentClaim
    form_class = PaymentClaimForm
    template_name = 'boq/claim_form.html'
    success_url = reverse_lazy('boq:claim_list')


class PaymentClaimDetailView(BOQViewMixin, DetailView):
    model = PaymentClaim
    template_name = 'boq/claim_detail.html'
    context_object_name = 'claim'
