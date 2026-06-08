import csv
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, FormView, View
from apps.accounts.mixins import CurrentProjectMixin, BOQViewMixin, FinancialWriteMixin
from apps.projects.models import Project
from .models import BOQItem, DailyProgressRecord, PaymentClaim
from .forms import BOQItemForm, DailyProgressRecordForm, PaymentClaimForm, BOQImportForm


class BOQItemListView(CurrentProjectMixin, BOQViewMixin, ListView):

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


class BOQItemCreateView(CurrentProjectMixin, FinancialWriteMixin, CreateView):

    model = BOQItem
    form_class = BOQItemForm
    template_name = 'boq/form.html'
    success_url = reverse_lazy('boq:list')

    def form_valid(self, form):
        messages.success(self.request, 'BOQ item created.')
        return super().form_valid(form)


class BOQItemUpdateView(CurrentProjectMixin, FinancialWriteMixin, UpdateView):

    model = BOQItem
    form_class = BOQItemForm
    template_name = 'boq/form.html'
    success_url = reverse_lazy('boq:list')


class BOQItemDeleteView(CurrentProjectMixin, FinancialWriteMixin, DeleteView):

    model = BOQItem
    template_name = 'boq/confirm_delete.html'
    success_url = reverse_lazy('boq:list')


class DailyProgressRecordListView(CurrentProjectMixin, BOQViewMixin, ListView):

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


class DailyProgressRecordCreateView(CurrentProjectMixin, FinancialWriteMixin, CreateView):

    model = DailyProgressRecord
    form_class = DailyProgressRecordForm
    template_name = 'boq/progress_form.html'
    success_url = reverse_lazy('boq:progress_list')

    def form_valid(self, form):
        messages.success(self.request, 'Progress recorded.')
        return super().form_valid(form)


class BulkProgressCreateView(CurrentProjectMixin, FinancialWriteMixin, View):
    """Bulk daily-progress entry: one form for all BOQ line items on a given date."""
    template_name = 'boq/bulk_progress_form.html'

    def _build_sections(self, project, post_data=None):
        """Return section list with line items annotated for the form."""
        all_items = list(
            BOQItem.objects.filter(project=project)
            .select_related('parent')
            .order_by('sort_key')
        )
        # Build cumulative quantities in one query
        cum_map = {
            row['boq_item_id']: row['total']
            for row in DailyProgressRecord.objects
                .filter(project=project)
                .values('boq_item_id')
                .annotate(total=Sum('daily_quantity'))
        }

        sections = []
        current_section = None
        for item in all_items:
            if item.item_type == 'header':
                current_section = {'header': item, 'rows': []}
                sections.append(current_section)
            else:
                cum = float(cum_map.get(item.pk) or 0)
                contract = float(item.contract_quantity or 0)
                pct = round(cum / contract * 100, 1) if contract else 0
                remaining = max(contract - cum, 0)
                row = {
                    'item': item,
                    'cum': cum,
                    'pct': pct,
                    'remaining': remaining,
                    'qty_input': post_data.get(f'qty_{item.pk}', '') if post_data else '',
                    'remarks_input': post_data.get(f'remarks_{item.pk}', '') if post_data else '',
                }
                if current_section:
                    current_section['rows'].append(row)
                else:
                    # Items without a header section
                    orphan = next((s for s in sections if s['header'] is None), None)
                    if not orphan:
                        orphan = {'header': None, 'rows': []}
                        sections.insert(0, orphan)
                    orphan['rows'].append(row)
        return sections

    def get(self, request):
        project = self.current_project
        if not project:
            messages.warning(request, 'กรุณาเลือกโครงการก่อน')
            return redirect('boq:progress_list')
        sections = self._build_sections(project)
        return render(request, self.template_name, {
            'project': project,
            'sections': sections,
            'today': date.today().isoformat(),
        })

    def post(self, request):
        project_id = request.POST.get('project_id')
        if project_id:
            project = Project.objects.filter(pk=project_id).first()
        else:
            project = self.current_project
        if not project:
            return redirect('boq:progress_list')

        record_date_str = request.POST.get('record_date', '').strip()
        if not record_date_str:
            messages.error(request, 'กรุณาระบุวันที่')
            sections = self._build_sections(project, request.POST)
            return render(request, self.template_name, {
                'project': project, 'sections': sections,
                'today': date.today().isoformat(), 'post_date': record_date_str,
            })

        try:
            from datetime import datetime
            record_date = datetime.strptime(record_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'รูปแบบวันที่ไม่ถูกต้อง')
            sections = self._build_sections(project, request.POST)
            return render(request, self.template_name, {
                'project': project, 'sections': sections,
                'today': date.today().isoformat(),
            })

        created, skipped = 0, 0
        line_items = BOQItem.objects.filter(project=project, item_type='item')
        for item in line_items:
            qty_str = request.POST.get(f'qty_{item.pk}', '').strip()
            if not qty_str or qty_str == '0':
                continue
            try:
                qty = Decimal(qty_str)
                if qty <= 0:
                    continue
            except Exception:
                continue

            remarks = request.POST.get(f'remarks_{item.pk}', '').strip()
            allow_overrun = request.POST.get(f'overrun_{item.pk}') == '1'
            rec = DailyProgressRecord(
                project=project,
                boq_item=item,
                record_date=record_date,
                daily_quantity=qty,
                remarks=remarks,
                allow_overrun=allow_overrun,
            )
            try:
                rec.full_clean()
                rec.save()
                created += 1
            except Exception as e:
                skipped += 1
                import logging
                logging.getLogger(__name__).warning('DailyProgressRecord save failed pk=%s: %s', item.pk, e)

        if created:
            messages.success(request, f'บันทึก Progress {created} รายการ สำหรับวันที่ {record_date_str}')
        if skipped:
            messages.warning(request, f'ข้าม {skipped} รายการ (เกิน Contract Qty — ติ๊ก Allow Overrun เพื่อบันทึก)')
        if not created and not skipped:
            messages.warning(request, 'ไม่มีข้อมูลที่บันทึก กรุณากรอกปริมาณอย่างน้อย 1 รายการ')
            sections = self._build_sections(project, request.POST)
            return render(request, self.template_name, {
                'project': project, 'sections': sections,
                'today': date.today().isoformat(), 'post_date': record_date_str,
            })

        return redirect('boq:progress_list')


class PaymentClaimListView(CurrentProjectMixin, BOQViewMixin, ListView):

    model = PaymentClaim
    template_name = 'boq/claim_list.html'
    context_object_name = 'claims'
    paginate_by = 20


class PaymentClaimCreateView(CurrentProjectMixin, FinancialWriteMixin, CreateView):

    model = PaymentClaim
    form_class = PaymentClaimForm
    template_name = 'boq/claim_form.html'
    success_url = reverse_lazy('boq:claim_list')


class PaymentClaimDetailView(CurrentProjectMixin, BOQViewMixin, DetailView):

    model = PaymentClaim
    template_name = 'boq/claim_detail.html'
    context_object_name = 'claim'
