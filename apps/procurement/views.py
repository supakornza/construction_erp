from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from apps.accounts.mixins import AdminRequiredMixin, ApproverRequiredMixin
from .models import Supplier, PurchaseRequest, PurchaseOrder
from .forms import (SupplierForm, PurchaseRequestForm, PurchaseRequestItemFormSet,
                    PurchaseOrderForm, PurchaseOrderItemFormSet)


class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'procurement/supplier_list.html'
    context_object_name = 'suppliers'


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'procurement/supplier_form.html'
    success_url = reverse_lazy('procurement:supplier_list')


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'procurement/supplier_form.html'
    success_url = reverse_lazy('procurement:supplier_list')


class PurchaseRequestListView(LoginRequiredMixin, ListView):
    model = PurchaseRequest
    template_name = 'procurement/pr_list.html'
    context_object_name = 'prs'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'requested_by')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class PurchaseRequestCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseRequest
    form_class = PurchaseRequestForm
    template_name = 'procurement/pr_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['item_formset'] = PurchaseRequestItemFormSet(self.request.POST or None)
        return ctx

    def form_valid(self, form):
        item_fs = PurchaseRequestItemFormSet(self.request.POST)
        if item_fs.is_valid():
            with transaction.atomic():
                form.instance.requested_by = form.instance.requested_by or self.request.user
                self.object = form.save()
                item_fs.instance = self.object
                item_fs.save()
            messages.success(self.request, f'PR {self.object.pr_no} created.')
            return redirect('procurement:pr_detail', pk=self.object.pk)
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('procurement:pr_detail', kwargs={'pk': self.object.pk})


class PurchaseRequestDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseRequest
    template_name = 'procurement/pr_detail.html'
    context_object_name = 'pr'


class PurchaseOrderListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'procurement/po_list.html'
    context_object_name = 'pos'
    paginate_by = 20


class PurchaseOrderCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'procurement/po_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['item_formset'] = PurchaseOrderItemFormSet(self.request.POST or None)
        return ctx

    def form_valid(self, form):
        item_fs = PurchaseOrderItemFormSet(self.request.POST)
        if item_fs.is_valid():
            with transaction.atomic():
                self.object = form.save()
                item_fs.instance = self.object
                item_fs.save()
                total = sum(i.total_price for i in self.object.items.all())
                self.object.total_amount = total
                self.object.save()
            messages.success(self.request, f'PO {self.object.po_no} created.')
            return redirect('procurement:po_detail', pk=self.object.pk)
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('procurement:po_detail', kwargs={'pk': self.object.pk})


class PurchaseOrderDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'procurement/po_detail.html'
    context_object_name = 'po'
