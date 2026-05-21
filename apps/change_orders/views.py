from datetime import date
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View

from apps.accounts.mixins import ChangeOrderViewMixin, ChangeOrderWriteMixin, ChangeOrderApproveMixin
from apps.projects.models import Project
from .models import ChangeOrder, ChangeOrderItem
from .forms import ChangeOrderForm, ChangeOrderItemFormSet, RejectionForm


class ChangeOrderListView(ChangeOrderViewMixin, ListView):
    model = ChangeOrder
    template_name = 'change_orders/list.html'
    context_object_name = 'change_orders'
    paginate_by = 20

    def get_queryset(self):
        qs = ChangeOrder.objects.select_related('project', 'prepared_by').order_by('-initiated_date')
        project_id = self.request.GET.get('project')
        status     = self.request.GET.get('status')
        co_type    = self.request.GET.get('type')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if status:
            qs = qs.filter(status=status)
        if co_type:
            qs = qs.filter(type=co_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects']       = Project.objects.filter(status='Active')
        ctx['status_choices'] = ChangeOrder.STATUS_CHOICES
        ctx['type_choices']   = ChangeOrder.TYPE_CHOICES
        return ctx


class ChangeOrderCreateView(ChangeOrderWriteMixin, CreateView):
    model         = ChangeOrder
    form_class    = ChangeOrderForm
    template_name = 'change_orders/form.html'

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get('project')
        if project_id:
            initial['project'] = project_id
        initial['initiated_date'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['item_formset'] = ChangeOrderItemFormSet(self.request.POST)
        else:
            ctx['item_formset'] = ChangeOrderItemFormSet()
        ctx['title'] = 'New Change Order'
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        item_fs = ctx['item_formset']
        if not item_fs.is_valid():
            return self.form_invalid(form)
        with transaction.atomic():
            form.instance.prepared_by = self.request.user
            form.instance.co_no = ChangeOrder.generate_co_no(form.instance.project)
            self.object = form.save()
            item_fs.instance = self.object
            item_fs.save()
        messages.success(self.request, f'Change Order {self.object.co_no} created.')
        return redirect(reverse('change_orders:detail', kwargs={'pk': self.object.pk}))


class ChangeOrderDetailView(ChangeOrderViewMixin, DetailView):
    model             = ChangeOrder
    template_name     = 'change_orders/detail.html'
    context_object_name = 'co'

    def get_queryset(self):
        return ChangeOrder.objects.select_related(
            'project', 'prepared_by', 'reviewed_by', 'approved_by'
        ).prefetch_related('items__boq_item')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['items_total'] = sum(item.amount for item in self.object.items.all())
        return ctx


class ChangeOrderUpdateView(ChangeOrderWriteMixin, UpdateView):
    model         = ChangeOrder
    form_class    = ChangeOrderForm
    template_name = 'change_orders/form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(ChangeOrder, pk=kwargs['pk'])
        if not obj.is_editable:
            messages.error(request, f'Change Order {obj.co_no} cannot be edited in {obj.status} status.')
            return redirect('change_orders:detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['item_formset'] = ChangeOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            ctx['item_formset'] = ChangeOrderItemFormSet(instance=self.object)
        ctx['title'] = f'Edit {self.object.co_no}'
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        item_fs = ctx['item_formset']
        if not item_fs.is_valid():
            return self.form_invalid(form)
        with transaction.atomic():
            self.object = form.save()
            item_fs.instance = self.object
            item_fs.save()
        messages.success(self.request, f'Change Order {self.object.co_no} updated.')
        return redirect(reverse('change_orders:detail', kwargs={'pk': self.object.pk}))

    def get_success_url(self):
        return reverse('change_orders:detail', kwargs={'pk': self.object.pk})


class ChangeOrderDeleteView(ChangeOrderWriteMixin, DeleteView):
    model         = ChangeOrder
    template_name = 'change_orders/confirm_delete.html'
    success_url   = reverse_lazy('change_orders:list')

    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(ChangeOrder, pk=kwargs['pk'])
        if obj.status not in ('Draft', 'Cancelled'):
            messages.error(request, 'Only Draft or Cancelled change orders can be deleted.')
            return redirect('change_orders:detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f'Change Order {obj.co_no} deleted.')
        return super().delete(request, *args, **kwargs)


# ── Workflow Actions ──────────────────────────────────────────────────────────

class ChangeOrderSubmitView(ChangeOrderWriteMixin, View):
    def post(self, request, pk):
        co = get_object_or_404(ChangeOrder, pk=pk)
        if co.status != 'Draft':
            messages.error(request, 'Only Draft change orders can be submitted.')
        else:
            co.status         = 'Submitted'
            co.submitted_date = date.today()
            co.save(update_fields=['status', 'submitted_date'])
            messages.success(request, f'{co.co_no} submitted for review.')
        return redirect('change_orders:detail', pk=pk)


class ChangeOrderReviewView(ChangeOrderApproveMixin, View):
    def post(self, request, pk):
        co = get_object_or_404(ChangeOrder, pk=pk)
        if co.status != 'Submitted':
            messages.error(request, 'Only Submitted change orders can be moved to Under Review.')
        else:
            co.status      = 'UnderReview'
            co.reviewed_by = request.user
            co.save(update_fields=['status', 'reviewed_by'])
            messages.success(request, f'{co.co_no} is now Under Review.')
        return redirect('change_orders:detail', pk=pk)


class ChangeOrderApproveView(ChangeOrderApproveMixin, View):
    def post(self, request, pk):
        co = get_object_or_404(ChangeOrder, pk=pk)
        if co.status not in ('Submitted', 'UnderReview'):
            messages.error(request, 'Change order cannot be approved in its current status.')
        else:
            co.status        = 'Approved'
            co.approved_by   = request.user
            co.approved_date = date.today()
            co.save(update_fields=['status', 'approved_by', 'approved_date'])
            messages.success(request, f'{co.co_no} approved.')
        return redirect('change_orders:detail', pk=pk)


class ChangeOrderRejectView(ChangeOrderApproveMixin, View):
    def get(self, request, pk):
        co   = get_object_or_404(ChangeOrder, pk=pk)
        form = RejectionForm()
        return render(request, 'change_orders/reject.html', {'co': co, 'form': form})

    def post(self, request, pk):
        co   = get_object_or_404(ChangeOrder, pk=pk)
        form = RejectionForm(request.POST)
        if not form.is_valid():
            return render(request, 'change_orders/reject.html', {'co': co, 'form': form})
        if co.status not in ('Submitted', 'UnderReview'):
            messages.error(request, 'Change order cannot be rejected in its current status.')
        else:
            co.status           = 'Rejected'
            co.rejection_reason = form.cleaned_data['rejection_reason']
            co.reviewed_by      = request.user
            co.save(update_fields=['status', 'rejection_reason', 'reviewed_by'])
            messages.warning(request, f'{co.co_no} rejected.')
        return redirect('change_orders:detail', pk=pk)


class ChangeOrderCancelView(ChangeOrderWriteMixin, View):
    def post(self, request, pk):
        co = get_object_or_404(ChangeOrder, pk=pk)
        if co.status == 'Approved':
            messages.error(request, 'Approved change orders cannot be cancelled.')
        else:
            co.status = 'Cancelled'
            co.save(update_fields=['status'])
            messages.warning(request, f'{co.co_no} cancelled.')
        return redirect('change_orders:detail', pk=pk)
