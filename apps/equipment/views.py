from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from apps.accounts.mixins import CurrentProjectMixin, ManagerRequiredMixin, OperationalViewMixin, OperationalUpdateMixin
from .models import Equipment, DailyEquipmentRecord, EquipmentPhoto
from .forms import EquipmentForm, DailyEquipmentRecordForm, EquipmentPhotoForm


class EquipmentListView(CurrentProjectMixin, OperationalViewMixin, ListView):

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


class EquipmentDetailView(CurrentProjectMixin, OperationalViewMixin, DetailView):

    model = Equipment
    template_name = 'equipment/detail.html'
    context_object_name = 'equipment'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['photos'] = self.object.photos.all()
        ctx['photo_form'] = EquipmentPhotoForm()
        ctx['recent_records'] = (
            self.object.dailyequipmentrecord_set
            .select_related('project')
            .order_by('-report_date')[:10]
        )
        return ctx


class EquipmentCreateView(CurrentProjectMixin, OperationalViewMixin, CreateView):

    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/form.html'

    def get_success_url(self):
        return reverse('equipment:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Equipment added.')
        return super().form_valid(form)


class EquipmentUpdateView(CurrentProjectMixin, OperationalUpdateMixin, UpdateView):

    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/form.html'

    def get_success_url(self):
        return reverse('equipment:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Equipment updated.')
        return super().form_valid(form)


class EquipmentDeleteView(ManagerRequiredMixin, DeleteView):
    model = Equipment
    template_name = 'equipment/confirm_delete.html'
    success_url = reverse_lazy('equipment:list')


class EquipmentPhotoUploadView(OperationalViewMixin, View):
    def post(self, request, pk):
        equipment = get_object_or_404(Equipment, pk=pk)
        form = EquipmentPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.equipment = equipment
            photo.save()
            messages.success(request, 'Photo uploaded.')
        else:
            messages.error(request, 'Invalid file. Please upload a valid image.')
        return redirect('equipment:detail', pk=pk)


class EquipmentPhotoDeleteView(OperationalUpdateMixin, View):
    def post(self, request, pk, photo_pk):
        photo = get_object_or_404(EquipmentPhoto, pk=photo_pk, equipment_id=pk)
        photo.image.delete(save=False)
        photo.delete()
        messages.success(request, 'Photo deleted.')
        return redirect('equipment:detail', pk=pk)


class DailyEquipmentRecordListView(CurrentProjectMixin, OperationalViewMixin, ListView):

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


class DailyEquipmentRecordCreateView(CurrentProjectMixin, OperationalViewMixin, CreateView):

    model = DailyEquipmentRecord
    form_class = DailyEquipmentRecordForm
    template_name = 'equipment/record_form.html'
    success_url = reverse_lazy('equipment:record_list')

    def form_valid(self, form):
        messages.success(self.request, 'Equipment record added.')
        return super().form_valid(form)


class DailyEquipmentRecordUpdateView(CurrentProjectMixin, OperationalUpdateMixin, UpdateView):

    model = DailyEquipmentRecord
    form_class = DailyEquipmentRecordForm
    template_name = 'equipment/record_form.html'
    success_url = reverse_lazy('equipment:record_list')


class DailyEquipmentRecordDeleteView(CurrentProjectMixin, ManagerRequiredMixin, DeleteView):

    model = DailyEquipmentRecord
    template_name = 'equipment/confirm_delete.html'
    success_url = reverse_lazy('equipment:record_list')
