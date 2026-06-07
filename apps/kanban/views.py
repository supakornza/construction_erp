import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from apps.accounts.mixins import CurrentProjectMixin
from apps.projects.models import Project

from .forms import KanbanTaskForm
from .models import KanbanTask

COLUMNS = [
    {'key': KanbanTask.COLUMN_TODO,        'label': 'To Do',       'icon': 'far fa-circle',       'color': '#64748b'},
    {'key': KanbanTask.COLUMN_IN_PROGRESS, 'label': 'In Progress', 'icon': 'fas fa-spinner',      'color': '#0d6efd'},
    {'key': KanbanTask.COLUMN_IN_REVIEW,   'label': 'In Review',   'icon': 'far fa-eye',          'color': '#f59e0b'},
    {'key': KanbanTask.COLUMN_DONE,        'label': 'Done',        'icon': 'fas fa-check-circle', 'color': '#10b981'},
]


class KanbanBoardView(CurrentProjectMixin, LoginRequiredMixin, TemplateView):

    template_name = 'kanban/board.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project_id = self.request.GET.get('project')

        qs = KanbanTask.objects.select_related('project', 'assignee').order_by('order', '-created_at')
        if project_id:
            qs = qs.filter(project_id=project_id)

        task_list = list(qs)
        columns = []
        for col in COLUMNS:
            col_tasks = [t for t in task_list if t.column == col['key']]
            columns.append({**col, 'tasks': col_tasks, 'count': len(col_tasks)})

        ctx['columns'] = columns
        ctx['projects'] = Project.objects.order_by('project_name')
        ctx['selected_project_id'] = project_id
        ctx['total_tasks'] = len(task_list)
        return ctx


class KanbanTaskMoveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(KanbanTask, pk=pk)
        try:
            data = json.loads(request.body)
            column = data.get('column')
            ordered_ids = data.get('ordered_ids', [])
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'error': 'Invalid request'}, status=400)

        if column not in dict(KanbanTask.COLUMN_CHOICES):
            return JsonResponse({'error': 'Invalid column'}, status=400)

        task.column = column
        task.save(update_fields=['column', 'updated_at'])

        for i, tid in enumerate(ordered_ids):
            KanbanTask.objects.filter(pk=tid).update(order=i)

        return JsonResponse({'ok': True})


class KanbanTaskCreateView(CurrentProjectMixin, LoginRequiredMixin, CreateView):

    model = KanbanTask
    form_class = KanbanTaskForm
    template_name = 'kanban/task_form.html'
    success_url = reverse_lazy('kanban:board')

    def get_initial(self):
        initial = super().get_initial()
        col = self.request.GET.get('column', KanbanTask.COLUMN_TODO)
        if col in dict(KanbanTask.COLUMN_CHOICES):
            initial['column'] = col
        if pid := self.request.GET.get('project'):
            initial['project'] = pid
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Task created.')
        return super().form_valid(form)


class KanbanTaskUpdateView(CurrentProjectMixin, LoginRequiredMixin, UpdateView):

    model = KanbanTask
    form_class = KanbanTaskForm
    template_name = 'kanban/task_form.html'
    success_url = reverse_lazy('kanban:board')

    def form_valid(self, form):
        messages.success(self.request, 'Task updated.')
        return super().form_valid(form)


class KanbanTaskDeleteView(CurrentProjectMixin, LoginRequiredMixin, DeleteView):

    model = KanbanTask
    template_name = 'kanban/confirm_delete.html'
    success_url = reverse_lazy('kanban:board')

    def form_valid(self, form):
        messages.success(self.request, 'Task deleted.')
        return super().form_valid(form)
