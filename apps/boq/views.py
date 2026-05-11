from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from apps.accounts.mixins import AdminRequiredMixin
from .models import BOQItem, DailyProgressRecord, PaymentClaim
from .forms import BOQItemForm, DailyProgressRecordForm, PaymentClaimForm


class BOQItemListView(LoginRequiredMixin, ListView):
    model = BOQItem
    template_name = 'boq/list.html'
    context_object_name = 'items'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('project')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.all()
        return ctx


class BOQItemCreateView(LoginRequiredMixin, CreateView):
    model = BOQItem
    form_class = BOQItemForm
    template_name = 'boq/form.html'
    success_url = reverse_lazy('boq:list')

    def form_valid(self, form):
        messages.success(self.request, 'BOQ item created.')
        return super().form_valid(form)


class BOQItemUpdateView(LoginRequiredMixin, UpdateView):
    model = BOQItem
    form_class = BOQItemForm
    template_name = 'boq/form.html'
    success_url = reverse_lazy('boq:list')


class BOQItemDeleteView(AdminRequiredMixin, DeleteView):
    model = BOQItem
    template_name = 'boq/confirm_delete.html'
    success_url = reverse_lazy('boq:list')


class DailyProgressRecordListView(LoginRequiredMixin, ListView):
    model = DailyProgressRecord
    template_name = 'boq/progress_list.html'
    context_object_name = 'records'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'boq_item')
        project_id = self.request.GET.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs


class DailyProgressRecordCreateView(LoginRequiredMixin, CreateView):
    model = DailyProgressRecord
    form_class = DailyProgressRecordForm
    template_name = 'boq/progress_form.html'
    success_url = reverse_lazy('boq:progress_list')

    def form_valid(self, form):
        messages.success(self.request, 'Progress recorded.')
        return super().form_valid(form)


class PaymentClaimListView(LoginRequiredMixin, ListView):
    model = PaymentClaim
    template_name = 'boq/claim_list.html'
    context_object_name = 'claims'
    paginate_by = 20


class PaymentClaimCreateView(LoginRequiredMixin, CreateView):
    model = PaymentClaim
    form_class = PaymentClaimForm
    template_name = 'boq/claim_form.html'
    success_url = reverse_lazy('boq:claim_list')


class PaymentClaimDetailView(LoginRequiredMixin, DetailView):
    model = PaymentClaim
    template_name = 'boq/claim_detail.html'
    context_object_name = 'claim'
