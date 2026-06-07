from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from apps.accounts.mixins import CurrentProjectMixin, DocumentsMixin, ManagerRequiredMixin
from .models import Document, DocumentCategory, DocumentRevision
from .forms import DocumentForm, DocumentRevisionForm


class DocumentListView(CurrentProjectMixin, DocumentsMixin, ListView):

    model = Document
    template_name = 'documents/list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'category', 'uploaded_by')
        project_id = self.request.GET.get('project')
        status = self.request.GET.get('status')
        q = self.request.GET.get('q')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if status:
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(document_no__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.all()
        ctx['status_choices'] = Document.STATUS_CHOICES
        return ctx


class DocumentCreateView(CurrentProjectMixin, DocumentsMixin, CreateView):

    model = Document
    form_class = DocumentForm
    template_name = 'documents/form.html'
    success_url = reverse_lazy('documents:list')

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Document uploaded.')
        return super().form_valid(form)


class DocumentDetailView(CurrentProjectMixin, DocumentsMixin, DetailView):

    model = Document
    template_name = 'documents/detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['revisions'] = self.object.revisions.all()
        ctx['revision_form'] = DocumentRevisionForm()
        return ctx


class DocumentUpdateView(CurrentProjectMixin, DocumentsMixin, UpdateView):

    model = Document
    form_class = DocumentForm
    template_name = 'documents/form.html'

    def get_success_url(self):
        return reverse_lazy('documents:detail', kwargs={'pk': self.object.pk})


class DocumentDeleteView(CurrentProjectMixin, ManagerRequiredMixin, DeleteView):

    model = Document
    template_name = 'documents/confirm_delete.html'
    success_url = reverse_lazy('documents:list')


class AddRevisionView(CurrentProjectMixin, DocumentsMixin, CreateView):

    model = DocumentRevision
    form_class = DocumentRevisionForm
    template_name = 'documents/revision_form.html'

    def get_document(self):
        return get_object_or_404(Document, pk=self.kwargs['document_pk'])

    def form_valid(self, form):
        form.instance.document = self.get_document()
        form.instance.revised_by = self.request.user
        form.save()
        messages.success(self.request, 'Revision added.')
        return redirect('documents:detail', pk=self.kwargs['document_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['document'] = self.get_document()
        return ctx
