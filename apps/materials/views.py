from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from django.utils import timezone
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
            deliveries.values('source')
            .annotate(quantity=Coalesce(Sum('quantity'), 0, output_field=DecimalField()), count=Count('id'))
            .order_by('-quantity')[:8]
        )
        project_rows = list(
            deliveries.values('project__contract_no', 'project__project_name')
            .annotate(quantity=Coalesce(Sum('quantity'), 0, output_field=DecimalField()), count=Count('id'))
            .order_by('-quantity')[:8]
        )
        today = timezone.localdate()
        truck_rows_today = list(
            MaterialDelivery.objects
            .filter(delivery_date=today)
            .exclude(truck_no='')
            .values('truck_no')
            .annotate(trips=Count('id'), quantity=Coalesce(Sum('quantity'), 0, output_field=DecimalField()))
            .order_by('-trips')
        )
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
            'project_rows': project_rows,
            'truck_rows_today': truck_rows_today,
            'today': today,
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
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'material')
        project_id = self.request.GET.get('project')
        material_id = self.request.GET.get('material')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if material_id:
            qs = qs.filter(material_id=material_id)
        return qs

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        ctx['materials'] = Material.objects.all()
        return ctx


class MaterialDeliveryCreateView(MaterialsWriteMixin, CreateView):
    model = MaterialDelivery
    form_class = MaterialDeliveryForm
    template_name = 'materials/delivery_form.html'
    success_url = reverse_lazy('materials:delivery_list')

    def form_valid(self, form):
        messages.success(self.request, 'Delivery recorded.')
        return super().form_valid(form)


class MaterialDeliveryUpdateView(MaterialsWriteMixin, UpdateView):
    model = MaterialDelivery
    form_class = MaterialDeliveryForm
    template_name = 'materials/delivery_form.html'
    success_url = reverse_lazy('materials:delivery_list')


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
