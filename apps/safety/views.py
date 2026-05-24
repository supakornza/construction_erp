from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from apps.accounts.mixins import SafetyViewMixin, SafetyWriteMixin, SafetyDeleteMixin
from .models import ToolboxMeeting, SafetyInspection, IncidentReport, JSEARecord
from .forms import ToolboxMeetingForm, SafetyInspectionForm, IncidentReportForm, JSEARecordForm


class SafetyIndexView(View):
    def get(self, request):
        return redirect('safety:inspection_list')


class ToolboxMeetingListView(SafetyViewMixin, ListView):
    model = ToolboxMeeting
    template_name = 'safety/toolbox_list.html'
    context_object_name = 'meetings'
    paginate_by = 20


class ToolboxMeetingCreateView(SafetyWriteMixin, CreateView):
    model = ToolboxMeeting
    form_class = ToolboxMeetingForm
    template_name = 'safety/toolbox_form.html'
    success_url = reverse_lazy('safety:toolbox_list')

    def form_valid(self, form):
        messages.success(self.request, 'Toolbox meeting recorded.')
        return super().form_valid(form)


class ToolboxMeetingUpdateView(SafetyWriteMixin, UpdateView):
    model = ToolboxMeeting
    form_class = ToolboxMeetingForm
    template_name = 'safety/toolbox_form.html'
    success_url = reverse_lazy('safety:toolbox_list')


class SafetyInspectionListView(SafetyViewMixin, ListView):
    model = SafetyInspection
    template_name = 'safety/inspection_list.html'
    context_object_name = 'inspections'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'inspector')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class SafetyInspectionCreateView(SafetyWriteMixin, CreateView):
    model = SafetyInspection
    form_class = SafetyInspectionForm
    template_name = 'safety/inspection_form.html'
    success_url = reverse_lazy('safety:inspection_list')

    def form_valid(self, form):
        messages.success(self.request, 'Safety inspection recorded.')
        return super().form_valid(form)


class SafetyInspectionDetailView(SafetyViewMixin, DetailView):
    model = SafetyInspection
    template_name = 'safety/inspection_detail.html'
    context_object_name = 'inspection'


class SafetyInspectionUpdateView(SafetyWriteMixin, UpdateView):
    model = SafetyInspection
    form_class = SafetyInspectionForm
    template_name = 'safety/inspection_form.html'
    success_url = reverse_lazy('safety:inspection_list')


class IncidentReportListView(SafetyViewMixin, ListView):
    model = IncidentReport
    template_name = 'safety/incident_list.html'
    context_object_name = 'incidents'
    paginate_by = 20


class IncidentReportCreateView(SafetyWriteMixin, CreateView):
    model = IncidentReport
    form_class = IncidentReportForm
    template_name = 'safety/incident_form.html'
    success_url = reverse_lazy('safety:incident_list')


class IncidentReportDetailView(SafetyViewMixin, DetailView):
    model = IncidentReport
    template_name = 'safety/incident_detail.html'
    context_object_name = 'incident'


class IncidentReportUpdateView(SafetyWriteMixin, UpdateView):
    model = IncidentReport
    form_class = IncidentReportForm
    template_name = 'safety/incident_form.html'
    success_url = reverse_lazy('safety:incident_list')


class JSEARecordListView(SafetyViewMixin, ListView):
    model = JSEARecord
    template_name = 'safety/jsea_list.html'
    context_object_name = 'jsea_records'
    paginate_by = 20


class JSEARecordCreateView(SafetyWriteMixin, CreateView):
    model = JSEARecord
    form_class = JSEARecordForm
    template_name = 'safety/jsea_form.html'
    success_url = reverse_lazy('safety:jsea_list')


class ToolboxMeetingDeleteView(SafetyDeleteMixin, DeleteView):
    model = ToolboxMeeting
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('safety:toolbox_list')


class SafetyInspectionDeleteView(SafetyDeleteMixin, DeleteView):
    model = SafetyInspection
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('safety:inspection_list')


class IncidentReportDeleteView(SafetyDeleteMixin, DeleteView):
    model = IncidentReport
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('safety:incident_list')


class JSEARecordDeleteView(SafetyDeleteMixin, DeleteView):
    model = JSEARecord
    template_name = 'safety/confirm_delete.html'
    success_url = reverse_lazy('safety:jsea_list')
