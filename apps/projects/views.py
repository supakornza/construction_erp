from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from apps.accounts.mixins import AdminRequiredMixin
from .models import Project, Stakeholder, WorkArea
from .forms import ProjectForm, StakeholderForm, WorkAreaForm


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get('status')
        q = self.request.GET.get('q')
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(project_name__icontains=q) | qs.filter(contract_no__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Project.STATUS_CHOICES
        ctx['current_status'] = self.request.GET.get('status', '')
        return ctx


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'
    success_url = reverse_lazy('projects:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Project created successfully.')
        return super().form_valid(form)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stakeholders'] = self.object.stakeholders.all()
        ctx['work_areas'] = self.object.work_areas.all()
        return ctx


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Project updated successfully.')
        return super().form_valid(form)


class ProjectDeleteView(AdminRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/confirm_delete.html'
    success_url = reverse_lazy('projects:list')

    def form_valid(self, form):
        messages.success(self.request, 'Project deleted.')
        return super().form_valid(form)


class StakeholderCreateView(LoginRequiredMixin, CreateView):
    model = Stakeholder
    form_class = StakeholderForm
    template_name = 'projects/stakeholder_form.html'

    def get_project(self):
        return Project.objects.get(pk=self.kwargs['project_pk'])

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, 'Stakeholder added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.kwargs['project_pk']})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['project'] = self.get_project()
        return ctx


class WorkAreaCreateView(LoginRequiredMixin, CreateView):
    model = WorkArea
    form_class = WorkAreaForm
    template_name = 'projects/work_area_form.html'

    def get_project(self):
        return Project.objects.get(pk=self.kwargs['project_pk'])

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, 'Work area added.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.kwargs['project_pk']})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['project'] = self.get_project()
        return ctx


class WorkAreaUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkArea
    form_class = WorkAreaForm
    template_name = 'projects/work_area_form.html'

    def get_project(self):
        return self.object.project

    def form_valid(self, form):
        messages.success(self.request, 'Work area updated.')
        return super().form_valid(form)

    def get_success_url(self):
        return f"{reverse_lazy('projects:detail', kwargs={'pk': self.object.project.pk})}#work-areas"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['project'] = self.get_project()
        return ctx
