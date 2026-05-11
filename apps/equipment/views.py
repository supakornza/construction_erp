from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from apps.accounts.mixins import AdminRequiredMixin
from .models import Equipment, DailyEquipmentRecord
from .forms import EquipmentForm, DailyEquipmentRecordForm


class EquipmentListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = 'equipment/list.html'
    context_object_name = 'equipment_list'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('category', 'project')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs


class EquipmentCreateView(LoginRequiredMixin, CreateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/form.html'
    success_url = reverse_lazy('equipment:list')

    def form_valid(self, form):
        messages.success(self.request, 'Equipment added.')
        return super().form_valid(form)


class EquipmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/form.html'
    success_url = reverse_lazy('equipment:list')


class EquipmentDeleteView(AdminRequiredMixin, DeleteView):
    model = Equipment
    template_name = 'equipment/confirm_delete.html'
    success_url = reverse_lazy('equipment:list')


class DailyEquipmentRecordListView(LoginRequiredMixin, ListView):
    model = DailyEquipmentRecord
    template_name = 'equipment/record_list.html'
    context_object_name = 'records'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'equipment', 'equipment__category')
        project_id = self.request.GET.get('project')
        date_str = self.request.GET.get('date')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if date_str:
            qs = qs.filter(report_date=date_str)
        return qs

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        return ctx


class DailyEquipmentRecordCreateView(LoginRequiredMixin, CreateView):
    model = DailyEquipmentRecord
    form_class = DailyEquipmentRecordForm
    template_name = 'equipment/record_form.html'
    success_url = reverse_lazy('equipment:record_list')

    def form_valid(self, form):
        messages.success(self.request, 'Equipment record added.')
        return super().form_valid(form)


class DailyEquipmentRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = DailyEquipmentRecord
    form_class = DailyEquipmentRecordForm
    template_name = 'equipment/record_form.html'
    success_url = reverse_lazy('equipment:record_list')


class DailyEquipmentRecordDeleteView(AdminRequiredMixin, DeleteView):
    model = DailyEquipmentRecord
    template_name = 'equipment/confirm_delete.html'
    success_url = reverse_lazy('equipment:record_list')
