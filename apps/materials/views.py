import json
import tempfile
from pathlib import Path
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from apps.accounts.mixins import MaterialsViewMixin, MaterialsWriteMixin, MaterialsDeleteMixin
from apps.projects.models import Project
from .models import Material, MaterialDelivery, MaterialUsage, get_stock_balance
from .forms import MaterialForm, MaterialDeliveryForm, MaterialUsageForm


def _delivery_filters(request):
    today = timezone.localdate()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if not date_from:
        date_from = (today - timezone.timedelta(days=29)).isoformat()
    if not date_to:
        date_to = today.isoformat()
    return {
        'project_id': request.GET.get('project') or '',
        'material_id': request.GET.get('material') or '',
        'date_from': date_from,
        'date_to': date_to,
    }


def _filtered_deliveries(filters):
    qs = MaterialDelivery.objects.select_related('project', 'material', 'material__category')
    if filters['project_id']:
        qs = qs.filter(project_id=filters['project_id'])
    if filters['material_id']:
        qs = qs.filter(material_id=filters['material_id'])
    if filters['date_from']:
        qs = qs.filter(delivery_date__gte=filters['date_from'])
    if filters['date_to']:
        qs = qs.filter(delivery_date__lte=filters['date_to'])
    return qs


class MaterialDeliveryDashboardView(MaterialsViewMixin, TemplateView):
    template_name = 'materials/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        filters = _delivery_filters(self.request)
        deliveries = _filtered_deliveries(filters)
        amount_expr = ExpressionWrapper(
            Coalesce(F('quantity') * F('unit_price'), 0),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
        totals = deliveries.aggregate(
            total_quantity=Coalesce(Sum('quantity'), 0, output_field=DecimalField()),
            total_amount=Coalesce(Sum(amount_expr), 0, output_field=DecimalField(max_digits=18, decimal_places=2)),
            delivery_count=Count('id'),
        )
        daily_rows = list(
            deliveries.values('delivery_date')
            .annotate(quantity=Coalesce(Sum('quantity'), 0, output_field=DecimalField()))
            .order_by('delivery_date')
        )
        material_rows = list(
            deliveries.values('material__name', 'material__unit')
            .annotate(quantity=Coalesce(Sum('quantity'), 0, output_field=DecimalField()), count=Count('id'))
            .order_by('-quantity')[:10]
        )
        source_rows = list(
            deliveries.annotate(
                source_label=Coalesce(F('source_area__name'), F('source'))
            )
            .exclude(source_label__isnull=True).exclude(source_label='')
            .values(name=F('source_label'))
            .annotate(quantity=Coalesce(Sum('quantity'), 0, output_field=DecimalField()), count=Count('id'))
            .order_by('-quantity')[:8]
        )
        # Truck KPI honours the filter date range so the dashboard reflects
        # what the user selected, not just `today`. When the user leaves the
        # filter at its default (last 30 days) the tile shows the whole range
        # and labels itself accordingly.
        today = timezone.localdate()
        truck_date_from = filters.get('date_from') or today.isoformat()
        truck_date_to   = filters.get('date_to')   or today.isoformat()
        truck_is_single_day = truck_date_from == truck_date_to
        truck_rows_today = list(
            MaterialDelivery.objects
            .filter(delivery_date__range=(truck_date_from, truck_date_to))
            .exclude(truck_no='')
            .values('truck_no')
            .annotate(trips=Count('id'), quantity=Coalesce(Sum('quantity'), 0, output_field=DecimalField()))
            .order_by('-trips')
        )

        # รถเข้า Stockpile (date filtered) แยกตามโครงการ + แหล่งที่มา
        truck_source_today = list(
            MaterialDelivery.objects
            .filter(delivery_date__range=(truck_date_from, truck_date_to))
            .annotate(source_label=Coalesce(F('source_area__name'), F('source')))
            .values('project__id', 'project__contract_no', 'project__project_name', 'source_label')
            .annotate(
                truck_count=Count('truck_no', distinct=True),
                trips=Count('id'),
                quantity=Coalesce(Sum('quantity'), 0, output_field=DecimalField()),
            )
            .order_by('project__contract_no', '-quantity')
        )
        project_today_map = {}
        for row in truck_source_today:
            pid = row['project__id']
            if pid not in project_today_map:
                project_today_map[pid] = {
                    'contract_no': row['project__contract_no'],
                    'project_name': row['project__project_name'],
                    'total_trips': 0,
                    'total_qty': 0.0,
                    'by_source': [],
                }
            project_today_map[pid]['total_trips'] += row['trips']
            project_today_map[pid]['total_qty'] += float(row['quantity'] or 0)
            project_today_map[pid]['by_source'].append({
                'source': row['source_label'] or '—',
                'trips': row['trips'],
                'truck_count': row['truck_count'],
                'quantity': float(row['quantity'] or 0),
            })
        trucks_today_by_project = sorted(project_today_map.values(), key=lambda x: x['contract_no'] or '')

        # Rock & Sand stock from Project Controls for selected project
        rock_stock = sand_stock = None
        selected_project_id = filters.get('project_id')
        if selected_project_id:
            from apps.project_controls.models import RockDailyRecord, SandDailyRecord
            rock_latest = RockDailyRecord.objects.filter(project_id=selected_project_id).order_by('-record_date').first()
            if rock_latest:
                rock_stock = {
                    'delivered': float(rock_latest.tct_accum_ton),
                    'placed': float(rock_latest.placed_accum_ton),
                    'balance': float(rock_latest.tct_accum_ton - rock_latest.placed_accum_ton),
                    'date': rock_latest.record_date,
                    'daily_delivered': float(rock_latest.tct_daily_ton),
                    'daily_placed': float(rock_latest.placed_daily_ton),
                    'trucks': rock_latest.tct_trucks,
                    'trips': rock_latest.tct_trips,
                }
            sand_latest = SandDailyRecord.objects.filter(project_id=selected_project_id).order_by('-record_date').first()
            if sand_latest:
                sand_stock = {
                    'delivered': float(sand_latest.total_accum_ton),
                    'placed': float(sand_latest.total_placed),
                    'tct_stock': float(sand_latest.remaining_tct),
                    'mtp3_stock': float(sand_latest.remaining_mtp3),
                    'date': sand_latest.record_date,
                    'daily_delivered': float(sand_latest.total_daily_ton),
                    'tct_trucks': sand_latest.tct_trucks,
                    'tct_trips': sand_latest.tct_trips,
                }

        ctx.update({
            'filters': filters,
            'projects': Project.objects.filter(status='Active'),
            'materials': Material.objects.select_related('category'),
            'total_quantity': totals['total_quantity'],
            'total_amount': totals['total_amount'],
            'delivery_count': totals['delivery_count'],
            'latest_delivery': deliveries.order_by('-delivery_date', '-id').first(),
            'recent_deliveries': deliveries.order_by('-delivery_date', '-id')[:10],
            'daily_labels': [row['delivery_date'].isoformat() for row in daily_rows],
            'daily_quantities': [float(row['quantity'] or 0) for row in daily_rows],
            'material_rows': material_rows,
            'source_rows': source_rows,
            'truck_rows_today': truck_rows_today,
            'trucks_today_by_project': trucks_today_by_project,
            'today': today,
            'truck_date_from': truck_date_from,
            'truck_date_to': truck_date_to,
            'truck_is_single_day': truck_is_single_day,
            'rock_stock': rock_stock,
            'sand_stock': sand_stock,
        })
        return ctx


class MaterialListView(MaterialsViewMixin, ListView):
    model = Material
    template_name = 'materials/list.html'
    context_object_name = 'materials'


class MaterialCreateView(MaterialsWriteMixin, CreateView):
    model = Material
    form_class = MaterialForm
    template_name = 'materials/form.html'
    success_url = reverse_lazy('materials:list')

    def form_valid(self, form):
        messages.success(self.request, 'Material added.')
        return super().form_valid(form)


class MaterialUpdateView(MaterialsWriteMixin, UpdateView):
    model = Material
    form_class = MaterialForm
    template_name = 'materials/form.html'
    success_url = reverse_lazy('materials:list')


class MaterialDeliveryListView(MaterialsViewMixin, ListView):
    model = MaterialDelivery
    template_name = 'materials/delivery_list.html'
    context_object_name = 'deliveries'
    paginate_by = 50

    _SORT_MAP = {
        'date': 'delivery_date', '-date': '-delivery_date',
        'time': 'delivery_time', '-time': '-delivery_time',
        'created': 'created_at', '-created': '-created_at',
        'project': 'project__contract_no', '-project': '-project__contract_no',
        'material': 'material__name', '-material': '-material__name',
        'source': 'source_area__name', '-source': '-source_area__name',
        'truck': 'truck_no', '-truck': '-truck_no',
        'dn': 'delivery_note_no', '-dn': '-delivery_note_no',
        'qty': 'quantity', '-qty': '-quantity',
        'price': 'unit_price', '-price': '-unit_price',
    }
    DEFAULT_SORT = '-created'

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'material', 'source_area')
        p = self.request.GET
        if p.get('project'):
            qs = qs.filter(project_id=p['project'])
        if p.get('material'):
            qs = qs.filter(material_id=p['material'])
        if p.get('date_from'):
            qs = qs.filter(delivery_date__gte=p['date_from'])
        if p.get('date_to'):
            qs = qs.filter(delivery_date__lte=p['date_to'])
        if p.get('source', '').strip():
            q = p['source'].strip()
            qs = qs.filter(Q(source__icontains=q) | Q(source_area__name__icontains=q))
        if p.get('truck_no', '').strip():
            qs = qs.filter(truck_no__icontains=p['truck_no'].strip())
        if p.get('dn', '').strip():
            qs = qs.filter(delivery_note_no__icontains=p['dn'].strip())
        sort_key = p.get('sort', '') or self.DEFAULT_SORT
        order = self._SORT_MAP.get(sort_key, self._SORT_MAP[self.DEFAULT_SORT])
        return qs.order_by(order, '-id')

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        ctx['materials'] = Material.objects.all()
        ctx['current_sort'] = self.request.GET.get('sort') or self.DEFAULT_SORT
        ctx['view_mode'] = self.request.GET.get('view', 'table')
        get_copy = self.request.GET.copy()
        get_copy.pop('page', None)
        ctx['filter_params'] = get_copy.urlencode()
        # Duplicate delivery_note_no detection (per project)
        dup_pairs = (
            MaterialDelivery.objects
            .exclude(delivery_note_no='')
            .values('project_id', 'delivery_note_no')
            .annotate(c=Count('id')).filter(c__gt=1)
        )
        ctx['duplicate_dns_keys'] = {f"{d['project_id']}|{d['delivery_note_no']}" for d in dup_pairs}
        return ctx


def _attach_ocr_metadata(form_instance, request):
    """Pull OCR audit fields out of the POST body (set by the form's JS after
    a successful ocr-preview call) and onto the model instance."""
    tmpl = request.POST.get('ocr_template', '').strip()
    if not tmpl:
        return
    form_instance.ocr_template = tmpl[:50]
    raw = request.POST.get('ocr_raw_text', '')
    if raw:
        form_instance.ocr_raw_text = raw[:20000]
    try:
        c = float(request.POST.get('ocr_confidence', ''))
        form_instance.ocr_confidence = round(c, 3)
    except (TypeError, ValueError):
        pass
    form_instance.ocr_processed_at = timezone.now()


class MaterialDeliveryCreateView(MaterialsWriteMixin, CreateView):
    model = MaterialDelivery
    form_class = MaterialDeliveryForm
    template_name = 'materials/delivery_form.html'
    success_url = reverse_lazy('materials:delivery_list')

    def form_valid(self, form):
        _attach_ocr_metadata(form.instance, self.request)
        messages.success(self.request, 'Delivery recorded.')
        return super().form_valid(form)


class MaterialDeliveryUpdateView(MaterialsWriteMixin, UpdateView):
    model = MaterialDelivery
    form_class = MaterialDeliveryForm
    template_name = 'materials/delivery_form.html'
    success_url = reverse_lazy('materials:delivery_list')

    def form_valid(self, form):
        _attach_ocr_metadata(form.instance, self.request)
        return super().form_valid(form)


class MaterialDeliveryDeleteView(MaterialsDeleteMixin, DeleteView):
    model = MaterialDelivery
    template_name = 'materials/confirm_delete.html'
    success_url = reverse_lazy('materials:delivery_list')


class MaterialUsageListView(MaterialsViewMixin, ListView):
    model = MaterialUsage
    template_name = 'materials/usage_list.html'
    context_object_name = 'usages'
    paginate_by = 30


class MaterialUsageCreateView(MaterialsWriteMixin, CreateView):
    model = MaterialUsage
    form_class = MaterialUsageForm
    template_name = 'materials/usage_form.html'
    success_url = reverse_lazy('materials:usage_list')


class StockBalanceView(MaterialsViewMixin, ListView):
    model = Material
    template_name = 'materials/stock.html'
    context_object_name = 'materials'

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project
        ctx = super().get_context_data(**kwargs)
        project_id = self.request.GET.get('project')
        ctx['projects'] = Project.objects.filter(status='Active')
        ctx['selected_project'] = None
        ctx['stock_data'] = []
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)
                ctx['selected_project'] = project
                materials = Material.objects.all()
                stock_data = []
                for mat in materials:
                    bal = get_stock_balance(project, mat)
                    if bal['delivered'] > 0 or bal['used'] > 0:
                        stock_data.append({'material': mat, **bal})
                ctx['stock_data'] = stock_data
            except Project.DoesNotExist:
                pass
        return ctx


# ─── OCR preview endpoint ──────────────────────────────────────────────

MAX_OCR_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_OCR_MIME = {'image/jpeg', 'image/jpg', 'image/png', 'image/webp'}


@require_POST
@login_required
def ocr_preview(request):
    """Accept a multipart 'image' upload, run OCR + template extraction,
    return JSON with pre-fill values for the delivery form.

    Response shape: {ok, template, supplier, fields, field_confidence,
                     warnings, raw_text, duration_ms, overall_confidence}
    """
    img = request.FILES.get('image')
    if not img:
        return JsonResponse({'ok': False, 'error': 'no image uploaded'}, status=400)
    if img.size > MAX_OCR_IMAGE_BYTES:
        return JsonResponse({'ok': False, 'error': 'image too large (max 10 MB)'}, status=400)
    if img.content_type and img.content_type.lower() not in ALLOWED_OCR_MIME:
        return JsonResponse(
            {'ok': False, 'error': f'unsupported type: {img.content_type}'}, status=400,
        )

    # Lazy import — keeps server boot fast and avoids pytesseract import cost
    # when this endpoint is not used.
    from apps.materials.ocr.service import run_ocr
    from apps.materials.ocr.normalize import normalize, kg_to_unit
    from apps.materials.ocr.template_engine import extract

    # Tesseract reads from disk; write upload to a temp file.
    with tempfile.NamedTemporaryFile(suffix=Path(img.name).suffix or '.jpg',
                                     delete=False) as tmp:
        for chunk in img.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        try:
            ocr_result = run_ocr(tmp_path)
        except Exception as e:
            return JsonResponse(
                {'ok': False, 'error': f'OCR engine failed: {e}'}, status=500,
            )
        normalized = normalize(ocr_result.raw_text)
        ext = extract(ocr_result.words, normalized)

        # Map extracted fields to form field names + apply unit conversion
        # (quantity_kg -> quantity, converted to material.unit if FK resolved)
        fields_out: dict = {}
        confidence_out: dict = {}
        project_id = request.POST.get('project') or ''

        for k, fv in ext.fields.items():
            v = fv.value
            if k == 'quantity_kg':
                continue  # handled below with material context
            if k == 'material_name':
                continue  # handled below with fuzzy match
            if k == 'delivery_note_no':
                fields_out['delivery_note_no'] = str(v) if v else ''
            elif k == 'truck_no':
                fields_out['truck_no'] = str(v) if v else ''
            elif k == 'source':
                fields_out['source'] = str(v) if v else ''
            elif k == 'delivery_date':
                fields_out['delivery_date'] = v
            elif k == 'delivery_time':
                fields_out['delivery_time'] = v
            confidence_out[k] = round(fv.confidence, 2)

        # Material fuzzy-match against actual DB rows
        material_id = None
        material_name = None
        if 'material_name' in ext.fields:
            from rapidfuzz import process as fz_process
            mat_text = (ext.fields['material_name'].value or '').strip()
            if mat_text:
                candidates = list(Material.objects.values_list('id', 'name', 'unit'))
                if candidates:
                    names = [c[1] for c in candidates]
                    best = fz_process.extractOne(mat_text, names)
                    if best and best[1] >= 65:   # score 0..100
                        matched_idx = best[2]
                        material_id, matched_name, matched_unit = candidates[matched_idx]
                        material_name = matched_name
                        confidence_out['material_id'] = round(best[1] / 100.0, 2)
                        # quantity conversion: kg -> ton if material.unit is ton
                        if 'quantity_kg' in ext.fields:
                            qkg = ext.fields['quantity_kg'].value
                            if qkg is not None:
                                qty = kg_to_unit(float(qkg), matched_unit or '')
                                fields_out['quantity'] = str(qty)
                                confidence_out['quantity'] = round(
                                    ext.fields['quantity_kg'].confidence, 2,
                                )

        if material_id is not None:
            fields_out['material'] = str(material_id)
            fields_out['_material_display'] = material_name
        elif 'quantity_kg' in ext.fields:
            # quantity available but no material matched — pass raw kg so
            # the user sees it (they'll pick the material manually and may
            # need to adjust unit)
            qkg = ext.fields['quantity_kg'].value
            if qkg is not None:
                fields_out['quantity'] = str(qkg)
                fields_out['_quantity_unit_hint'] = 'kg'
                confidence_out['quantity'] = round(
                    ext.fields['quantity_kg'].confidence, 2,
                )

        return JsonResponse({
            'ok': True,
            'template': ext.template_key,
            'supplier': ext.template_supplier,
            'detect_score': ext.detect_score,
            'overall_confidence': round(ocr_result.avg_confidence, 2),
            'fields': fields_out,
            'field_confidence': confidence_out,
            'warnings': ext.warnings,
            'raw_text': normalized[:5000],   # cap response size
            'duration_ms': ocr_result.duration_ms,
        })
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
