from datetime import date

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import (
    ListView, CreateView, DetailView, UpdateView, TemplateView, View
)

from apps.accounts.mixins import CurrentProjectMixin, DrawingsViewMixin, DrawingsWriteMixin, DrawingsApproveMixin
from apps.notifications.utils import notify
from apps.projects.models import Project
from .models import Drawing, RFI
from .forms import DrawingForm, DrawingRevisionForm, RFIForm, RFIAnswerForm


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DrawingsDashboardView(DrawingsViewMixin, TemplateView):
    template_name = 'drawings/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx   = super().get_context_data(**kwargs)
        today = date.today()
        ctx['total_drawings']   = Drawing.objects.exclude(
            status__in=('Superseded', 'Cancelled')).count()
        ctx['ifc_drawings']     = Drawing.objects.filter(status='IFC').count()
        ctx['open_rfis']        = RFI.objects.filter(
            status__in=('Open', 'Submitted', 'UnderReview')).count()
        ctx['overdue_rfis']     = sum(
            1 for r in RFI.objects.filter(
                status__in=('Open', 'Submitted', 'UnderReview'),
                response_required_date__lt=today
            )
        )
        ctx['recent_drawings']  = (Drawing.objects
                                   .select_related('project', 'created_by')
                                   .order_by('-created_at')[:8])
        ctx['open_rfi_list']    = (RFI.objects
                                   .filter(status__in=('Open', 'Submitted', 'UnderReview'))
                                   .select_related('project', 'drawing')
                                   .order_by('response_required_date')[:10])
        return ctx


# ── Drawings ──────────────────────────────────────────────────────────────────

class DrawingListView(CurrentProjectMixin, DrawingsViewMixin, ListView):

    model               = Drawing
    template_name       = 'drawings/drawing_list.html'
    context_object_name = 'drawings'
    paginate_by         = 30

    def get_queryset(self):
        qs = Drawing.objects.select_related('project', 'created_by')
        if self.request.GET.get('project'):
            qs = qs.filter(project_id=self.request.GET['project'])
        if self.request.GET.get('discipline'):
            qs = qs.filter(discipline=self.request.GET['discipline'])
        if self.request.GET.get('status'):
            qs = qs.filter(status=self.request.GET['status'])
        if self.request.GET.get('q'):
            q  = self.request.GET['q']
            qs = qs.filter(Q(drawing_no__icontains=q) | Q(title__icontains=q))
        current_only = self.request.GET.get('current_only', '1')
        if current_only == '1':
            qs = qs.exclude(status__in=('Superseded', 'Cancelled'))
        return qs.order_by('drawing_no', 'revision')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['projects']          = Project.objects.filter(status='Active')
        ctx['discipline_choices'] = Drawing.DISCIPLINE_CHOICES
        ctx['status_choices']    = Drawing.STATUS_CHOICES
        return ctx


class DrawingCreateView(CurrentProjectMixin, DrawingsWriteMixin, CreateView):

    model         = Drawing
    form_class    = DrawingForm
    template_name = 'drawings/drawing_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        messages.success(self.request, f'Drawing {self.object.drawing_no} Rev.{self.object.revision} created.')
        return redirect(reverse('drawings:drawing_detail', kwargs={'pk': self.object.pk}))


class DrawingDetailView(CurrentProjectMixin, DrawingsViewMixin, DetailView):

    model               = Drawing
    template_name       = 'drawings/drawing_detail.html'
    context_object_name = 'drawing'

    def get_queryset(self):
        return Drawing.objects.select_related(
            'project', 'created_by', 'superseded_by'
        ).prefetch_related('rfis', 'supersedes')


class DrawingUpdateView(CurrentProjectMixin, DrawingsWriteMixin, UpdateView):

    model         = Drawing
    form_class    = DrawingForm
    template_name = 'drawings/drawing_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Drawing updated.')
        return reverse('drawings:drawing_detail', kwargs={'pk': self.object.pk})


class DrawingRevisionCreateView(CurrentProjectMixin, DrawingsWriteMixin, View):

    template_name = 'drawings/drawing_revision_form.html'

    def get(self, request, pk):
        original = get_object_or_404(Drawing, pk=pk)
        form = DrawingRevisionForm(initial={
            'status':      'IFR',
            'issue_date':  date.today(),
            'prepared_by': original.prepared_by,
            'description': original.description,
        })
        return render(request, self.template_name, {'form': form, 'original': original})

    def post(self, request, pk):
        original = get_object_or_404(Drawing, pk=pk)
        form = DrawingRevisionForm(request.POST, request.FILES)
        if form.is_valid():
            new_dwg             = form.save(commit=False)
            new_dwg.project     = original.project
            new_dwg.drawing_no  = original.drawing_no
            new_dwg.title       = original.title
            new_dwg.discipline  = original.discipline
            new_dwg.created_by  = request.user
            new_dwg.save()
            # Mark old revision as superseded
            original.status       = 'Superseded'
            original.superseded_by = new_dwg
            original.save(update_fields=['status', 'superseded_by'])
            messages.success(request, f'{new_dwg.drawing_no} Rev.{new_dwg.revision} issued.')
            return redirect(reverse('drawings:drawing_detail', kwargs={'pk': new_dwg.pk}))
        return render(request, self.template_name, {'form': form, 'original': original})


# ── RFI ───────────────────────────────────────────────────────────────────────

class RFIListView(CurrentProjectMixin, DrawingsViewMixin, ListView):

    model               = RFI
    template_name       = 'drawings/rfi_list.html'
    context_object_name = 'rfis'
    paginate_by         = 25

    def get_queryset(self):
        qs = RFI.objects.select_related('project', 'drawing', 'answered_by')
        if self.request.GET.get('project'):
            qs = qs.filter(project_id=self.request.GET['project'])
        if self.request.GET.get('status'):
            qs = qs.filter(status=self.request.GET['status'])
        if self.request.GET.get('priority'):
            qs = qs.filter(priority=self.request.GET['priority'])
        if self.request.GET.get('q'):
            q  = self.request.GET['q']
            qs = qs.filter(Q(rfi_no__icontains=q) | Q(subject__icontains=q))
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices']   = RFI.STATUS_CHOICES
        ctx['priority_choices'] = RFI.PRIORITY_CHOICES
        ctx['projects']         = Project.objects.filter(status='Active')
        ctx['today']            = date.today()
        return ctx


class RFICreateView(CurrentProjectMixin, DrawingsWriteMixin, CreateView):

    model         = RFI
    form_class    = RFIForm
    template_name = 'drawings/rfi_form.html'

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('project'):
            initial['project'] = self.request.GET['project']
        if self.request.GET.get('drawing'):
            initial['drawing'] = self.request.GET['drawing']
        initial.setdefault('submitted_date', date.today())
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        messages.success(self.request, f'{self.object.rfi_no} created.')
        return redirect(reverse('drawings:rfi_detail', kwargs={'pk': self.object.pk}))


class RFIDetailView(CurrentProjectMixin, DrawingsViewMixin, DetailView):

    model               = RFI
    template_name       = 'drawings/rfi_detail.html'
    context_object_name = 'rfi'

    def get_queryset(self):
        return RFI.objects.select_related(
            'project', 'drawing', 'answered_by', 'created_by'
        )


class RFIUpdateView(CurrentProjectMixin, DrawingsWriteMixin, UpdateView):

    model         = RFI
    form_class    = RFIForm
    template_name = 'drawings/rfi_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(RFI, pk=kwargs['pk'])
        if obj.status in ('Closed', 'Void'):
            messages.error(request, 'Closed/Void RFIs cannot be edited.')
            return redirect('drawings:rfi_detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, 'RFI updated.')
        return reverse('drawings:rfi_detail', kwargs={'pk': self.object.pk})


class RFISubmitView(CurrentProjectMixin, DrawingsWriteMixin, View):

    def post(self, request, pk):
        rfi = get_object_or_404(RFI, pk=pk)
        if rfi.status == 'Open':
            rfi.status         = 'Submitted'
            rfi.submitted_date = rfi.submitted_date or date.today()
            rfi.save(update_fields=['status', 'submitted_date'])
            messages.success(request, f'{rfi.rfi_no} submitted.')
        return redirect('drawings:rfi_detail', pk=pk)


class RFIReviewView(CurrentProjectMixin, DrawingsApproveMixin, View):

    def post(self, request, pk):
        rfi = get_object_or_404(RFI, pk=pk)
        if rfi.status == 'Submitted':
            rfi.status = 'UnderReview'
            rfi.save(update_fields=['status'])
            messages.success(request, f'{rfi.rfi_no} marked as Under Review.')
        return redirect('drawings:rfi_detail', pk=pk)


class RFIAnswerView(CurrentProjectMixin, DrawingsApproveMixin, View):

    template_name = 'drawings/rfi_answer.html'

    def get(self, request, pk):
        rfi  = get_object_or_404(RFI, pk=pk)
        form = RFIAnswerForm(instance=rfi, initial={'answered_date': date.today()})
        return render(request, self.template_name, {'rfi': rfi, 'form': form})

    def post(self, request, pk):
        rfi = get_object_or_404(RFI, pk=pk)
        if rfi.status not in ('Submitted', 'UnderReview'):
            messages.error(request, 'RFI must be Submitted or Under Review to answer.')
            return redirect('drawings:rfi_detail', pk=pk)
        form = RFIAnswerForm(request.POST, instance=rfi)
        if form.is_valid():
            obj             = form.save(commit=False)
            obj.status      = 'Answered'
            obj.answered_by = request.user
            obj.save()
            messages.success(request, f'{rfi.rfi_no} answered.')
            if obj.created_by and obj.created_by != request.user:
                notify(obj.created_by, 'rfi_answered',
                       f'{rfi.rfi_no} Answered',
                       f'RFI "{rfi.subject}" has been answered.',
                       reverse('drawings:rfi_detail', kwargs={'pk': rfi.pk}))
            return redirect('drawings:rfi_detail', pk=pk)
        return render(request, self.template_name, {'rfi': rfi, 'form': form})


class RFICloseView(CurrentProjectMixin, DrawingsApproveMixin, View):

    def post(self, request, pk):
        rfi = get_object_or_404(RFI, pk=pk)
        if rfi.status == 'Answered':
            rfi.status = 'Closed'
            rfi.save(update_fields=['status'])
            messages.success(request, f'{rfi.rfi_no} closed.')
        return redirect('drawings:rfi_detail', pk=pk)


class RFIVoidView(CurrentProjectMixin, DrawingsWriteMixin, View):

    def post(self, request, pk):
        rfi = get_object_or_404(RFI, pk=pk)
        if rfi.status not in ('Closed', 'Void'):
            rfi.status = 'Void'
            rfi.save(update_fields=['status'])
            messages.warning(request, f'{rfi.rfi_no} voided.')
        return redirect('drawings:rfi_detail', pk=pk)
