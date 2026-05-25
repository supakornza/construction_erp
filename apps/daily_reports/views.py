import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, FormView, View

from apps.utils import image_to_jpeg_bytes

from apps.accounts.mixins import (ApproverRequiredMixin, ManagerRequiredMixin,
                                   DailyReportViewMixin, DailyReportCreateMixin, DailyReportUpdateMixin)
from .models import DailyReport, DailyWorkActivity, DailyLookahead, DailyProblemRemark, DailyPhoto
from .forms import (DailyReportForm, RejectionForm,
                    DailyWorkActivityFormSet, DailyLookaheadFormSet,
                    DailyProblemFormSet, DailyPhotoFormSet)


class DailyReportListView(DailyReportViewMixin, ListView):
    model = DailyReport
    template_name = 'daily_reports/list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('project', 'prepared_by')
        project_id = self.request.GET.get('project')
        status = self.request.GET.get('status')
        if project_id:
            qs = qs.filter(project_id=project_id)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project
        ctx = super().get_context_data(**kwargs)
        ctx['projects'] = Project.objects.filter(status='Active')
        ctx['status_choices'] = DailyReport.STATUS_CHOICES
        return ctx


class DailyReportCreateView(DailyReportCreateMixin, CreateView):
    model = DailyReport
    form_class = DailyReportForm
    template_name = 'daily_reports/form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['activity_formset'] = DailyWorkActivityFormSet(self.request.POST)
            ctx['lookahead_formset'] = DailyLookaheadFormSet(self.request.POST)
            ctx['problem_formset'] = DailyProblemFormSet(self.request.POST)
            ctx['photo_formset'] = DailyPhotoFormSet(self.request.POST, self.request.FILES)
        else:
            ctx['activity_formset'] = DailyWorkActivityFormSet()
            ctx['lookahead_formset'] = DailyLookaheadFormSet()
            ctx['problem_formset'] = DailyProblemFormSet()
            ctx['photo_formset'] = DailyPhotoFormSet()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        activity_fs = ctx['activity_formset']
        lookahead_fs = ctx['lookahead_formset']
        problem_fs = ctx['problem_formset']
        photo_fs = ctx['photo_formset']
        if all([activity_fs.is_valid(), lookahead_fs.is_valid(), problem_fs.is_valid(), photo_fs.is_valid()]):
            with transaction.atomic():
                form.instance.prepared_by = form.instance.prepared_by or self.request.user
                self.object = form.save()
                for fs in [activity_fs, lookahead_fs, problem_fs, photo_fs]:
                    fs.instance = self.object
                    fs.save()
            messages.success(self.request, 'Daily report created.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('daily_reports:detail', kwargs={'pk': self.object.pk})


class DailyReportDetailView(DailyReportViewMixin, DetailView):
    model = DailyReport
    template_name = 'daily_reports/detail.html'
    context_object_name = 'report'

    def get_context_data(self, **kwargs):
        from apps.manpower.models import DailyManpowerRecord
        from apps.equipment.models import DailyEquipmentRecord
        from apps.materials.models import MaterialDelivery
        ctx = super().get_context_data(**kwargs)
        manpower_records = DailyManpowerRecord.objects.filter(report=self.object)
        ctx['manpower_records'] = manpower_records
        ctx['manpower_total'] = sum(m.quantity for m in manpower_records)
        ctx['equipment_records'] = DailyEquipmentRecord.objects.filter(report=self.object)
        ctx['material_deliveries'] = MaterialDelivery.objects.filter(
            project=self.object.project, delivery_date=self.object.report_date)
        return ctx


class DailyReportUpdateView(DailyReportUpdateMixin, UpdateView):
    model = DailyReport
    form_class = DailyReportForm
    template_name = 'daily_reports/form.html'

    def get_queryset(self):
        return DailyReport.objects.filter(status__in=['Draft', 'Rejected'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['activity_formset'] = DailyWorkActivityFormSet(self.request.POST, instance=self.object)
            ctx['lookahead_formset'] = DailyLookaheadFormSet(self.request.POST, instance=self.object)
            ctx['problem_formset'] = DailyProblemFormSet(self.request.POST, instance=self.object)
            ctx['photo_formset'] = DailyPhotoFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            ctx['activity_formset'] = DailyWorkActivityFormSet(instance=self.object)
            ctx['lookahead_formset'] = DailyLookaheadFormSet(instance=self.object)
            ctx['problem_formset'] = DailyProblemFormSet(instance=self.object)
            ctx['photo_formset'] = DailyPhotoFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        activity_fs = ctx['activity_formset']
        lookahead_fs = ctx['lookahead_formset']
        problem_fs = ctx['problem_formset']
        photo_fs = ctx['photo_formset']
        if all([activity_fs.is_valid(), lookahead_fs.is_valid(), problem_fs.is_valid(), photo_fs.is_valid()]):
            with transaction.atomic():
                self.object = form.save()
                for fs in [activity_fs, lookahead_fs, problem_fs, photo_fs]:
                    fs.instance = self.object
                    fs.save()
            messages.success(self.request, 'Report updated.')
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('daily_reports:detail', kwargs={'pk': self.object.pk})


class DailyReportDeleteView(ManagerRequiredMixin, DeleteView):
    model = DailyReport
    template_name = 'daily_reports/confirm_delete.html'
    success_url = reverse_lazy('daily_reports:list')


class SubmitReportView(DailyReportCreateMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(DailyReport, pk=pk, status='Draft')
        report.status = 'Submitted'
        report.save()
        messages.success(request, 'Report submitted for approval.')
        return redirect('daily_reports:detail', pk=pk)


class ApproveReportView(ApproverRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(DailyReport, pk=pk, status='Submitted')
        report.status = 'Approved'
        report.approved_by = request.user
        report.rejection_reason = ''
        report.save()
        messages.success(request, 'Report approved.')
        return redirect('daily_reports:detail', pk=pk)


class RejectReportView(ApproverRequiredMixin, FormView):
    form_class = RejectionForm
    template_name = 'daily_reports/reject.html'

    def get_report(self):
        return get_object_or_404(DailyReport, pk=self.kwargs['pk'], status='Submitted')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['report'] = self.get_report()
        return ctx

    def form_valid(self, form):
        report = self.get_report()
        report.status = 'Rejected'
        report.rejection_reason = form.cleaned_data['rejection_reason']
        report.save()
        messages.warning(self.request, 'Report rejected.')
        return redirect('daily_reports:detail', pk=report.pk)


class ExportPDFView(DailyReportViewMixin, View):
    def get(self, request, pk):
        from apps.reports.pdf_generator import generate_daily_report_pdf
        report = get_object_or_404(DailyReport, pk=pk)
        buffer = generate_daily_report_pdf(report)
        filename = f"DailyReport_{report.project.contract_no}_{report.report_date}.pdf"
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class PhotoReportPDFView(DailyReportViewMixin, View):
    def get(self, request, pk):
        from apps.reports.pdf_generator import generate_photo_report_pdf
        report = get_object_or_404(DailyReport, pk=pk)
        buffer = generate_photo_report_pdf(report)
        filename = f"PhotoReport_{report.project.contract_no}_{report.report_date}.pdf"
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


class PhotoPreviewView(DailyReportViewMixin, View):
    def get(self, request, pk, photo_pk):
        photo = get_object_or_404(DailyPhoto, pk=photo_pk, report_id=pk)
        if not photo.photo:
            raise Http404('Photo not found')

        try:
            jpeg_buf = image_to_jpeg_bytes(photo.photo.path)
        except Exception:
            return FileResponse(photo.photo.open('rb'), content_type='application/octet-stream')

        response = HttpResponse(jpeg_buf.getvalue(), content_type='image/jpeg')
        response['Cache-Control'] = 'private, max-age=86400'
        return response


class PhotoUploadView(DailyReportCreateMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(DailyReport, pk=pk)
        photo_file = request.FILES.get('photo')
        caption = request.POST.get('caption', '').strip()
        location = request.POST.get('location', '').strip()
        if photo_file and caption:
            try:
                jpeg_buf = image_to_jpeg_bytes(photo_file)
                base_name = os.path.splitext(photo_file.name)[0]
                photo_file = ContentFile(jpeg_buf.read(), name=f"{base_name}.jpg")
            except Exception:
                messages.error(request, 'ไม่สามารถอ่านไฟล์รูปได้ กรุณาใช้ไฟล์ JPG หรือ PNG')
                return redirect('daily_reports:detail', pk=pk)
            last_order = report.photos.aggregate(m=Max('sort_order'))['m'] or 0
            DailyPhoto.objects.create(
                report=report,
                photo=photo_file,
                caption=caption,
                location=location,
                sort_order=last_order + 1,
            )
            messages.success(request, 'Photo added.')
        else:
            messages.error(request, 'Photo file and caption are required.')
        return redirect('daily_reports:detail', pk=pk)


class PhotoDeleteView(DailyReportUpdateMixin, View):
    def post(self, request, pk, photo_pk):
        photo = get_object_or_404(DailyPhoto, pk=photo_pk, report_id=pk)
        photo.photo.delete(save=False)
        photo.delete()
        messages.success(request, 'Photo deleted.')
        return redirect('daily_reports:detail', pk=pk)
