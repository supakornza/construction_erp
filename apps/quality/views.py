from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from apps.accounts.mixins import CurrentProjectMixin, QualityViewMixin, QualityInspectorMixin, QualityEngineerMixin

from .forms import (
    InspectionRequestForm,
    NonConformanceForm,
    PunchListForm,
    QualityCheckpointForm,
)
from .models import InspectionRequest, NonConformance, PunchList, QualityCheckpoint
from .services import get_quality_dashboard_tables, get_quality_metrics


class QualityDashboardView(QualityViewMixin, TemplateView):
    template_name = 'quality/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['metrics'] = get_quality_metrics()
        context['tables'] = get_quality_dashboard_tables(limit=8)
        return context


class InspectionRequestListView(CurrentProjectMixin, QualityViewMixin, ListView):

    model = InspectionRequest
    template_name = 'quality/inspection_list.html'
    context_object_name = 'inspections'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project', 'boq_item', 'requested_by', 'inspected_by')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class InspectionRequestCreateView(CurrentProjectMixin, QualityInspectorMixin, CreateView):

    model = InspectionRequest
    form_class = InspectionRequestForm
    template_name = 'quality/form.html'
    success_url = reverse_lazy('quality:inspection_list')
    extra_context = {'title': 'New Inspection Request', 'back_url_name': 'quality:inspection_list'}

    def form_valid(self, form):
        messages.success(self.request, 'Inspection request saved.')
        return super().form_valid(form)


class InspectionRequestUpdateView(CurrentProjectMixin, QualityInspectorMixin, UpdateView):

    model = InspectionRequest
    form_class = InspectionRequestForm
    template_name = 'quality/form.html'
    success_url = reverse_lazy('quality:inspection_list')
    extra_context = {'title': 'Edit Inspection Request', 'back_url_name': 'quality:inspection_list'}


class NonConformanceListView(CurrentProjectMixin, QualityViewMixin, ListView):

    model = NonConformance
    template_name = 'quality/ncr_list.html'
    context_object_name = 'ncrs'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project', 'responsible_person', 'boq_item')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class NonConformanceCreateView(CurrentProjectMixin, QualityInspectorMixin, CreateView):

    model = NonConformance
    form_class = NonConformanceForm
    template_name = 'quality/form.html'
    success_url = reverse_lazy('quality:ncr_list')
    extra_context = {'title': 'New NCR', 'back_url_name': 'quality:ncr_list'}

    def form_valid(self, form):
        messages.success(self.request, 'NCR saved.')
        return super().form_valid(form)


class NonConformanceUpdateView(CurrentProjectMixin, QualityInspectorMixin, UpdateView):

    model = NonConformance
    form_class = NonConformanceForm
    template_name = 'quality/form.html'
    success_url = reverse_lazy('quality:ncr_list')
    extra_context = {'title': 'Edit NCR', 'back_url_name': 'quality:ncr_list'}


class PunchListView(CurrentProjectMixin, QualityViewMixin, ListView):

    model = PunchList
    template_name = 'quality/punch_list.html'
    context_object_name = 'punch_items'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project', 'responsible_person')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class PunchListCreateView(CurrentProjectMixin, QualityInspectorMixin, CreateView):

    model = PunchList
    form_class = PunchListForm
    template_name = 'quality/form.html'
    success_url = reverse_lazy('quality:punch_list')
    extra_context = {'title': 'New Punch List Item', 'back_url_name': 'quality:punch_list'}

    def form_valid(self, form):
        messages.success(self.request, 'Punch list item saved.')
        return super().form_valid(form)


class PunchListUpdateView(CurrentProjectMixin, QualityInspectorMixin, UpdateView):

    model = PunchList
    form_class = PunchListForm
    template_name = 'quality/form.html'
    success_url = reverse_lazy('quality:punch_list')
    extra_context = {'title': 'Edit Punch List Item', 'back_url_name': 'quality:punch_list'}


class QualityCheckpointListView(CurrentProjectMixin, QualityViewMixin, ListView):

    model = QualityCheckpoint
    template_name = 'quality/checkpoint_list.html'
    context_object_name = 'checkpoints'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project', 'boq_item')
        active = self.request.GET.get('active')
        if active in ('0', '1'):
            queryset = queryset.filter(is_active=active == '1')
        return queryset


class QualityCheckpointCreateView(CurrentProjectMixin, QualityEngineerMixin, CreateView):

    model = QualityCheckpoint
    form_class = QualityCheckpointForm
    template_name = 'quality/form.html'
    success_url = reverse_lazy('quality:checkpoint_list')
    extra_context = {'title': 'New Quality Checkpoint', 'back_url_name': 'quality:checkpoint_list'}

    def form_valid(self, form):
        messages.success(self.request, 'Quality checkpoint saved.')
        return super().form_valid(form)


class QualityCheckpointUpdateView(CurrentProjectMixin, QualityEngineerMixin, UpdateView):

    model = QualityCheckpoint
    form_class = QualityCheckpointForm
    template_name = 'quality/form.html'
    success_url = reverse_lazy('quality:checkpoint_list')
    extra_context = {'title': 'Edit Quality Checkpoint', 'back_url_name': 'quality:checkpoint_list'}


class InspectionRequestDeleteView(CurrentProjectMixin, QualityEngineerMixin, DeleteView):

    model = InspectionRequest
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('quality:inspection_list')


class NonConformanceDeleteView(CurrentProjectMixin, QualityEngineerMixin, DeleteView):

    model = NonConformance
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('quality:ncr_list')


class PunchListDeleteView(CurrentProjectMixin, QualityEngineerMixin, DeleteView):

    model = PunchList
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('quality:punch_list')


class QualityCheckpointDeleteView(CurrentProjectMixin, QualityEngineerMixin, DeleteView):

    model = QualityCheckpoint
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('quality:checkpoint_list')
