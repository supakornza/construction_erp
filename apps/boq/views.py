import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, FormView, View
from apps.accounts.mixins import BOQViewMixin, FinancialWriteMixin
from .models import BOQItem, DailyProgressRecord, PaymentClaim
from .forms import BOQItemForm, DailyProgressRecordForm, PaymentClaimForm, BOQImportForm


class BOQItemListView(BOQViewMixin, ListView):
    model = BOQItem
    template_name = 'boq/list.html'
    context_object_name = 'items'

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'parent')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        from decimal import Decimal
        from apps.projects.models import Project
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.all()

        items = list(ctx['items'])
        by_id = {item.pk: item for item in items}

        # Depth (for indentation) and root ancestor (for section grouping).
        # Django templates reject underscore-prefixed attributes, so these
        # transient annotations use plain names.
        for item in items:
            level = 0
            root = item
            pid = item.parent_id
            while pid in by_id:
                level += 1
                root = by_id[pid]
                pid = root.parent_id
            item.level = level
            item.root = root

        # Bottom-up subtree subtotal rollup. `items` is in sort_key (pre-order
        # depth-first) order, so reversed() visits children before parents —
        # each item's running total can be folded straight into its parent's.
        subtotal = {item.pk: item.contract_amount for item in items}
        for item in reversed(items):
            if item.parent_id in by_id:
                subtotal[item.parent_id] += subtotal[item.pk]
        for item in items:
            item.subtotal = subtotal[item.pk]

        line_items = [i for i in items if i.item_type == 'item']
        grand_total = sum((i.contract_amount for i in line_items), Decimal('0'))

        def pct(amount):
            return (amount / grand_total * 100) if grand_total else Decimal('0')

        for item in items:
            item.percent = pct(item.subtotal)

        groups = []
        for root in [i for i in items if i.parent_id is None]:
            groups.append({
                'name': root.description,
                'items': [i for i in items if i.root.pk == root.pk and i.item_type == 'item'],
                'subtotal': subtotal[root.pk],
                'percent': pct(subtotal[root.pk]),
            })
        ctx['groups'] = groups
        ctx['grand_total'] = grand_total
        ctx['sections'] = sorted(groups, key=lambda g: g['subtotal'], reverse=True)
        ctx['top_items'] = [
            {'item': item, 'percent': pct(item.contract_amount)}
            for item in sorted(line_items, key=lambda i: i.contract_amount, reverse=True)[:10]
        ]
        return ctx


class BOQImportView(FinancialWriteMixin, FormView):
    form_class = BOQImportForm
    template_name = 'boq/import.html'
    success_url = reverse_lazy('boq:import')

    def form_valid(self, form):
        from .importers import import_boq_csv
        result = import_boq_csv(
            project=form.cleaned_data['project'],
            uploaded_file=form.cleaned_data['csv_file'],
            duplicate_action=form.cleaned_data['duplicate_action'],
        )
        if result['created']:
            messages.success(self.request, f"Imported {len(result['created'])} BOQ item(s).")
        if result['skipped']:
            messages.warning(self.request, f"Skipped {len(result['skipped'])} row(s) — see details below.")
        return self.render_to_response(self.get_context_data(form=self.form_class(), result=result))


class BOQImportTemplateView(FinancialWriteMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="boq_import_template.csv"'
        response.write('﻿')
        writer = csv.writer(response)
        writer.writerow(['รหัส', 'รายการ', 'หน่วย', 'ปริมาณ', 'ราคาต่อหน่วย'])
        writer.writerow(['1', 'ก่อสร้างคันหินวางบนฐานรากเสาเข็ม', '', '', ''])
        writer.writerow(['1.1', 'งานดำเนินการเพื่อการก่อสร้างงานหินถมป้องกันการกัดเซาะ', '', '', ''])
        writer.writerow(['1.1.1', 'จัดทำท่าขึ้นลงสำหรับวัสดุก่อสร้าง (Steel Platform ขนาด 216 ตร.ม.)', 'ตร.ม.', '216', '14583'])
        return response


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
