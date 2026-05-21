from datetime import date

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import (
    ListView, CreateView, DetailView, UpdateView, TemplateView, View
)

from apps.accounts.mixins import SubcontractorViewMixin, SubcontractorWriteMixin, SubcontractorApproveMixin
from apps.projects.models import Project
from .models import Subcontractor, SubcontractorContract, PaymentClaim
from .forms import (
    SubcontractorForm, SubcontractorContractForm, WorkItemFormSet,
    PaymentClaimForm, ClaimCertifyForm, ClaimPayForm,
)


# ── Dashboard ─────────────────────────────────────────────────────────────────

class SubcontractorDashboardView(SubcontractorViewMixin, TemplateView):
    template_name = 'subcontractors/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_subcontractors']  = Subcontractor.objects.filter(status='Active').count()
        ctx['active_contracts']      = SubcontractorContract.objects.filter(status='Active').count()
        ctx['total_contract_value']  = (SubcontractorContract.objects
                                        .filter(status__in=('Active', 'Completed'))
                                        .aggregate(t=Sum('contract_value'))['t'] or 0)
        ctx['total_paid']            = (PaymentClaim.objects.filter(status='Paid')
                                        .aggregate(t=Sum('net_payable'))['t'] or 0)
        ctx['pending_claims']        = PaymentClaim.objects.filter(
            status__in=('Submitted', 'Certified')).count()
        ctx['recent_contracts']      = (SubcontractorContract.objects
                                        .select_related('project', 'subcontractor')
                                        .order_by('-created_at')[:8])
        ctx['pending_payment_claims'] = (PaymentClaim.objects
                                         .filter(status__in=('Submitted', 'Certified'))
                                         .select_related('contract__subcontractor', 'contract__project')
                                         .order_by('-claim_date')[:10])
        return ctx


# ── Subcontractor Master ───────────────────────────────────────────────────────

class SubcontractorListView(SubcontractorViewMixin, ListView):
    model               = Subcontractor
    template_name       = 'subcontractors/contractor_list.html'
    context_object_name = 'subcontractors'
    paginate_by         = 25

    def get_queryset(self):
        qs = Subcontractor.objects.annotate(
            active_contract_count=Count('contracts', filter=Q(contracts__status='Active'))
        )
        if self.request.GET.get('status'):
            qs = qs.filter(status=self.request.GET['status'])
        if self.request.GET.get('category'):
            qs = qs.filter(category=self.request.GET['category'])
        if self.request.GET.get('q'):
            qs = qs.filter(name__icontains=self.request.GET['q'])
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category_choices'] = Subcontractor.CATEGORY_CHOICES
        ctx['status_choices']   = Subcontractor.STATUS_CHOICES
        return ctx


class SubcontractorCreateView(SubcontractorWriteMixin, CreateView):
    model         = Subcontractor
    form_class    = SubcontractorForm
    template_name = 'subcontractors/contractor_form.html'

    def get_success_url(self):
        messages.success(self.request, f'Subcontractor "{self.object.name}" created.')
        return reverse('subcontractors:contractor_detail', kwargs={'pk': self.object.pk})


class SubcontractorDetailView(SubcontractorViewMixin, DetailView):
    model               = Subcontractor
    template_name       = 'subcontractors/contractor_detail.html'
    context_object_name = 'subcontractor'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        contracts = self.object.contracts.select_related('project').order_by('-created_at')
        ctx['contracts']            = contracts
        ctx['total_contract_value'] = contracts.aggregate(t=Sum('contract_value'))['t'] or 0
        ctx['total_paid']           = (PaymentClaim.objects
                                       .filter(contract__subcontractor=self.object, status='Paid')
                                       .aggregate(t=Sum('net_payable'))['t'] or 0)
        return ctx


class SubcontractorUpdateView(SubcontractorWriteMixin, UpdateView):
    model         = Subcontractor
    form_class    = SubcontractorForm
    template_name = 'subcontractors/contractor_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Subcontractor updated.')
        return reverse('subcontractors:contractor_detail', kwargs={'pk': self.object.pk})


# ── Contracts ─────────────────────────────────────────────────────────────────

class ContractListView(SubcontractorViewMixin, ListView):
    model               = SubcontractorContract
    template_name       = 'subcontractors/contract_list.html'
    context_object_name = 'contracts'
    paginate_by         = 20

    def get_queryset(self):
        qs = SubcontractorContract.objects.select_related('project', 'subcontractor')
        if self.request.GET.get('project'):
            qs = qs.filter(project_id=self.request.GET['project'])
        if self.request.GET.get('status'):
            qs = qs.filter(status=self.request.GET['status'])
        if self.request.GET.get('subcontractor'):
            qs = qs.filter(subcontractor_id=self.request.GET['subcontractor'])
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices']      = SubcontractorContract.STATUS_CHOICES
        ctx['projects']            = Project.objects.filter(status='Active')
        ctx['subcontractor_list']  = Subcontractor.objects.filter(status='Active').order_by('name')
        return ctx


class ContractCreateView(SubcontractorWriteMixin, CreateView):
    model         = SubcontractorContract
    form_class    = SubcontractorContractForm
    template_name = 'subcontractors/contract_form.html'

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('project'):
            initial['project'] = self.request.GET['project']
        if self.request.GET.get('subcontractor'):
            initial['subcontractor'] = self.request.GET['subcontractor']
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['work_item_formset'] = (WorkItemFormSet(self.request.POST)
                                    if self.request.POST else WorkItemFormSet())
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        fs  = ctx['work_item_formset']
        with transaction.atomic():
            form.instance.created_by = self.request.user
            self.object = form.save()
            if fs.is_valid():
                fs.instance = self.object
                fs.save()
        messages.success(self.request, f'Contract {self.object.contract_no} created.')
        return redirect(reverse('subcontractors:contract_detail', kwargs={'pk': self.object.pk}))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ContractDetailView(SubcontractorViewMixin, DetailView):
    model               = SubcontractorContract
    template_name       = 'subcontractors/contract_detail.html'
    context_object_name = 'contract'

    def get_queryset(self):
        return SubcontractorContract.objects.select_related(
            'project', 'subcontractor', 'created_by'
        ).prefetch_related('work_items', 'payment_claims')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['work_items_total'] = sum(item.amount for item in self.object.work_items.all())
        ctx['claims'] = (self.object.payment_claims
                         .select_related('certified_by', 'created_by')
                         .order_by('-claim_date'))
        return ctx


class ContractUpdateView(SubcontractorWriteMixin, UpdateView):
    model         = SubcontractorContract
    form_class    = SubcontractorContractForm
    template_name = 'subcontractors/contract_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['work_item_formset'] = (WorkItemFormSet(self.request.POST, instance=self.object)
                                    if self.request.POST
                                    else WorkItemFormSet(instance=self.object))
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        fs  = ctx['work_item_formset']
        with transaction.atomic():
            self.object = form.save()
            if fs.is_valid():
                fs.instance = self.object
                fs.save()
        messages.success(self.request, 'Contract updated.')
        return redirect(reverse('subcontractors:contract_detail', kwargs={'pk': self.object.pk}))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ContractStatusView(SubcontractorApproveMixin, View):
    def post(self, request, pk):
        contract = get_object_or_404(SubcontractorContract, pk=pk)
        action = request.POST.get('action')
        transitions = {
            'activate':  ('Draft',   'Active',     'Contract activated.'),
            'complete':  ('Active',  'Completed',  'Contract marked as completed.'),
            'suspend':   ('Active',  'Suspended',  'Contract suspended.'),
            'reactivate':('Suspended','Active',    'Contract reactivated.'),
            'terminate': (None,      'Terminated', 'Contract terminated.'),
        }
        if action in transitions:
            required_from, new_status, msg = transitions[action]
            if required_from is None or contract.status == required_from:
                contract.status = new_status
                contract.save(update_fields=['status'])
                messages.success(request, msg)
            else:
                messages.error(request, f'Cannot perform this action on a {contract.status} contract.')
        return redirect('subcontractors:contract_detail', pk=pk)


# ── Payment Claims ─────────────────────────────────────────────────────────────

class PaymentClaimCreateView(SubcontractorWriteMixin, CreateView):
    model         = PaymentClaim
    form_class    = PaymentClaimForm
    template_name = 'subcontractors/claim_form.html'

    def _get_contract(self):
        return get_object_or_404(SubcontractorContract, pk=self.kwargs['contract_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['contract'] = self._get_contract()
        return ctx

    def get_initial(self):
        return {**super().get_initial(), 'claim_date': date.today()}

    def form_valid(self, form):
        contract = self._get_contract()
        obj = form.save(commit=False)
        obj.contract   = contract
        obj.created_by = self.request.user
        obj.save()
        messages.success(self.request, f'Payment claim {obj.claim_no} created.')
        return redirect(reverse('subcontractors:claim_detail', kwargs={'pk': obj.pk}))


class PaymentClaimDetailView(SubcontractorViewMixin, DetailView):
    model               = PaymentClaim
    template_name       = 'subcontractors/claim_detail.html'
    context_object_name = 'claim'

    def get_queryset(self):
        return PaymentClaim.objects.select_related(
            'contract__project', 'contract__subcontractor',
            'certified_by', 'created_by'
        )


class PaymentClaimSubmitView(SubcontractorWriteMixin, View):
    def post(self, request, pk):
        claim = get_object_or_404(PaymentClaim, pk=pk)
        if claim.status == 'Draft':
            claim.status = 'Submitted'
            claim.save(update_fields=['status'])
            messages.success(request, f'{claim.claim_no} submitted for certification.')
        return redirect('subcontractors:claim_detail', pk=pk)


class PaymentClaimCertifyView(SubcontractorApproveMixin, View):
    template_name = 'subcontractors/claim_certify.html'

    def _initial_certify(self, claim):
        retention = round(float(claim.claimed_amount) * float(claim.contract.retention_pct) / 100, 2)
        return {
            'certified_amount':   claim.claimed_amount,
            'retention_deducted': retention,
            'net_payable':        float(claim.claimed_amount) - retention,
            'certified_date':     date.today(),
        }

    def get(self, request, pk):
        claim = get_object_or_404(PaymentClaim, pk=pk)
        form  = ClaimCertifyForm(instance=claim, initial=self._initial_certify(claim))
        return render(request, self.template_name, {'claim': claim, 'form': form})

    def post(self, request, pk):
        claim = get_object_or_404(PaymentClaim, pk=pk)
        if claim.status != 'Submitted':
            messages.error(request, 'Only submitted claims can be certified.')
            return redirect('subcontractors:claim_detail', pk=pk)
        form = ClaimCertifyForm(request.POST, instance=claim)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status       = 'Certified'
            obj.certified_by = request.user
            obj.save()
            messages.success(request, f'{claim.claim_no} certified.')
            return redirect('subcontractors:claim_detail', pk=pk)
        return render(request, self.template_name, {'claim': claim, 'form': form})


class PaymentClaimPayView(SubcontractorApproveMixin, View):
    template_name = 'subcontractors/claim_pay.html'

    def get(self, request, pk):
        claim = get_object_or_404(PaymentClaim, pk=pk)
        form  = ClaimPayForm(instance=claim, initial={'paid_date': date.today()})
        return render(request, self.template_name, {'claim': claim, 'form': form})

    def post(self, request, pk):
        claim = get_object_or_404(PaymentClaim, pk=pk)
        if claim.status != 'Certified':
            messages.error(request, 'Only certified claims can be marked as paid.')
            return redirect('subcontractors:claim_detail', pk=pk)
        form = ClaimPayForm(request.POST, instance=claim)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status = 'Paid'
            obj.save()
            messages.success(request, f'{claim.claim_no} marked as paid.')
            return redirect('subcontractors:claim_detail', pk=pk)
        return render(request, self.template_name, {'claim': claim, 'form': form})


class PaymentClaimRejectView(SubcontractorApproveMixin, View):
    def post(self, request, pk):
        claim = get_object_or_404(PaymentClaim, pk=pk)
        if claim.status in ('Submitted', 'Certified'):
            claim.status = 'Rejected'
            claim.save(update_fields=['status'])
            messages.warning(request, f'{claim.claim_no} rejected.')
        return redirect('subcontractors:claim_detail', pk=pk)
