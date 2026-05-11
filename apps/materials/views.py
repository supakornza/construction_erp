from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from apps.accounts.mixins import AdminRequiredMixin
from .models import Material, MaterialDelivery, MaterialUsage, get_stock_balance
from .forms import MaterialForm, MaterialDeliveryForm, MaterialUsageForm


class MaterialListView(LoginRequiredMixin, ListView):
    model = Material
    template_name = 'materials/list.html'
    context_object_name = 'materials'


class MaterialCreateView(LoginRequiredMixin, CreateView):
    model = Material
    form_class = MaterialForm
    template_name = 'materials/form.html'
    success_url = reverse_lazy('materials:list')

    def form_valid(self, form):
        messages.success(self.request, 'Material added.')
        return super().form_valid(form)


class MaterialUpdateView(LoginRequiredMixin, UpdateView):
    model = Material
    form_class = MaterialForm
    template_name = 'materials/form.html'
    success_url = reverse_lazy('materials:list')


class MaterialDeliveryListView(LoginRequiredMixin, ListView):
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


class MaterialDeliveryCreateView(LoginRequiredMixin, CreateView):
    model = MaterialDelivery
    form_class = MaterialDeliveryForm
    template_name = 'materials/delivery_form.html'
    success_url = reverse_lazy('materials:delivery_list')

    def form_valid(self, form):
        messages.success(self.request, 'Delivery recorded.')
        return super().form_valid(form)


class MaterialDeliveryUpdateView(LoginRequiredMixin, UpdateView):
    model = MaterialDelivery
    form_class = MaterialDeliveryForm
    template_name = 'materials/delivery_form.html'
    success_url = reverse_lazy('materials:delivery_list')


class MaterialDeliveryDeleteView(AdminRequiredMixin, DeleteView):
    model = MaterialDelivery
    template_name = 'materials/confirm_delete.html'
    success_url = reverse_lazy('materials:delivery_list')


class MaterialUsageListView(LoginRequiredMixin, ListView):
    model = MaterialUsage
    template_name = 'materials/usage_list.html'
    context_object_name = 'usages'
    paginate_by = 30


class MaterialUsageCreateView(LoginRequiredMixin, CreateView):
    model = MaterialUsage
    form_class = MaterialUsageForm
    template_name = 'materials/usage_form.html'
    success_url = reverse_lazy('materials:usage_list')


class StockBalanceView(LoginRequiredMixin, ListView):
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
