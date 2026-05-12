"""
Views for the Contractor Daily Report import workflow.
"""
import json
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.projects.models import Project

from .importer import build_template_workbook, parse_import_file
from .models import (
    ContractorImport,
    ContractorImportActivity,
    ContractorImportEquipment,
    ContractorImportLookahead,
    ContractorImportManpower,
    DailyLookahead,
    DailyReport,
    DailyWorkActivity,
)

# Weather mapping: contractor format → DailyReport choices
_WEATHER_TO_DR = {
    'Clear': 'Sunny',
    'Cloudy': 'Cloudy',
    'Windy': 'Partly Cloudy',
    'Raining': 'Rainy',
    'High Wave': 'Rainy',
    'Other': 'Partly Cloudy',
}


def _decimal_json_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class ImportListView(LoginRequiredMixin, View):
    def get(self, request):
        qs = ContractorImport.objects.select_related('project', 'uploaded_by', 'daily_report')
        project_filter = request.GET.get('project', '')
        status_filter = request.GET.get('status', '')
        if project_filter:
            qs = qs.filter(project_id=project_filter)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return render(request, 'daily_reports/import_list.html', {
            'imports': qs,
            'projects': Project.objects.order_by('project_name'),
            'project_filter': project_filter,
            'status_filter': status_filter,
            'status_choices': ContractorImport.STATUS_CHOICES,
        })


class ImportUploadView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'daily_reports/import_upload.html', {
            'projects': Project.objects.order_by('project_name'),
        })

    def post(self, request):
        project_id = request.POST.get('project')
        uploaded_file = request.FILES.get('import_file')

        if not project_id:
            messages.error(request, 'Please select a project.')
            return redirect('daily_reports:import_upload')
        if not uploaded_file:
            messages.error(request, 'Please upload an Excel file.')
            return redirect('daily_reports:import_upload')
        if not uploaded_file.name.endswith(('.xlsx', '.xlsm')):
            messages.error(request, 'Only .xlsx / .xlsm files are accepted.')
            return redirect('daily_reports:import_upload')

        project = get_object_or_404(Project, pk=project_id)

        try:
            parsed = parse_import_file(uploaded_file)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('daily_reports:import_upload')

        session_data = json.loads(json.dumps({
            'project_id': project.pk,
            'project_name': project.project_name,
            'contract_no': project.contract_no,
            **parsed,
        }, default=_decimal_json_default))

        request.session['contractor_import_preview'] = session_data
        return redirect('daily_reports:import_preview')


class ImportPreviewView(LoginRequiredMixin, View):
    def get(self, request):
        data = request.session.get('contractor_import_preview')
        if not data:
            messages.error(request, 'No import data. Please upload a file first.')
            return redirect('daily_reports:import_upload')
        return render(request, 'daily_reports/import_preview.html', {'data': data})

    def post(self, request):
        data = request.session.get('contractor_import_preview')
        if not data:
            messages.error(request, 'Session expired. Please upload the file again.')
            return redirect('daily_reports:import_upload')

        project = get_object_or_404(Project, pk=data['project_id'])
        report_date = date.fromisoformat(data['report_date'])

        # Create the ContractorImport header record
        ci = ContractorImport.objects.create(
            project=project,
            report_date=report_date,
            contractor_name=data.get('contractor_name', ''),
            weather_day=data.get('weather_day', 'Clear'),
            weather_night=data.get('weather_night', 'Clear'),
            wind_speed=data.get('wind_speed', ''),
            total_manpower=data.get('total_manpower', 0),
            prepared_by_name=data.get('prepared_by_name', ''),
            checked_by_name=data.get('checked_by_name', ''),
            remarks=data.get('remarks', ''),
            status='Pending',
            uploaded_by=request.user,
        )

        for eq in data.get('equipment_items', []):
            ContractorImportEquipment.objects.create(contractor_import=ci, **eq)

        for mp in data.get('manpower_items', []):
            ContractorImportManpower.objects.create(contractor_import=ci, **mp)

        for act in data.get('activities', []):
            ContractorImportActivity.objects.create(
                contractor_import=ci,
                item_no=act['item_no'],
                description=act['description'],
                location=act.get('location', ''),
                quantity=Decimal(act['quantity']) if act.get('quantity') else None,
                unit=act.get('unit', ''),
                problem=act.get('problem', ''),
                remarks=act.get('remarks', ''),
            )

        for la in data.get('lookaheads', []):
            ContractorImportLookahead.objects.create(
                contractor_import=ci,
                item_no=la['item_no'],
                description=la['description'],
                location=la.get('location', ''),
                quantity=Decimal(la['quantity']) if la.get('quantity') else None,
                unit=la.get('unit', ''),
                remarks=la.get('remarks', ''),
            )

        del request.session['contractor_import_preview']
        messages.success(request, f'Import #{ci.pk} saved. Review the data and create a Daily Report when ready.')
        return redirect('daily_reports:import_detail', pk=ci.pk)


class ImportDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        ci = get_object_or_404(
            ContractorImport.objects.select_related('project', 'uploaded_by', 'daily_report')
            .prefetch_related('equipment_items', 'manpower_items', 'activities', 'lookaheads'),
            pk=pk,
        )
        return render(request, 'daily_reports/import_detail.html', {'ci': ci})


class ImportCreateReportView(LoginRequiredMixin, View):
    """Convert a ContractorImport into an official DailyReport."""

    def post(self, request, pk):
        ci = get_object_or_404(ContractorImport, pk=pk)

        if ci.status == 'Imported':
            messages.warning(request, 'This import has already been applied to a daily report.')
            return redirect('daily_reports:import_detail', pk=pk)

        weather_morning = _WEATHER_TO_DR.get(ci.weather_day, 'Sunny')
        weather_afternoon = _WEATHER_TO_DR.get(ci.weather_night, 'Sunny')

        # Get or create the DailyReport for this project+date
        existing = DailyReport.objects.filter(project=ci.project, report_date=ci.report_date).first()
        if existing:
            dr = existing
            created = False
        else:
            dr = DailyReport.objects.create(
                project=ci.project,
                report_date=ci.report_date,
                weather_morning=weather_morning,
                weather_afternoon=weather_afternoon,
                prepared_by=request.user,
                remarks=(
                    f"Imported from contractor report. "
                    f"Contractor: {ci.contractor_name}. "
                    f"Prepared by: {ci.prepared_by_name}. "
                    f"Checked by: {ci.checked_by_name}.\n"
                    + ci.remarks
                ).strip(),
                status='Draft',
            )
            created = True

        # Append work activities
        for act in ci.activities.all():
            desc = f"[{act.location}] {act.description}" if act.location else act.description
            DailyWorkActivity.objects.create(
                report=dr,
                description=desc,
                quantity=act.quantity,
                unit=act.unit,
                remarks='; '.join(filter(None, [act.problem, act.remarks])),
            )

        # Append lookaheads
        next_day = ci.report_date + timedelta(days=1)
        for la in ci.lookaheads.all():
            desc = f"[{la.location}] {la.description}" if la.location else la.description
            DailyLookahead.objects.create(
                report=dr,
                planned_activity=desc,
                planned_date=next_day,
                responsible_person=ci.contractor_name or '-',
            )

        ci.daily_report = dr
        ci.status = 'Imported'
        ci.save(update_fields=['daily_report', 'status'])

        verb = 'created' if created else 'updated'
        messages.success(request, f'Daily report for {ci.report_date} {verb} successfully.')
        return redirect('daily_reports:detail', pk=dr.pk)


class ImportDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        ci = get_object_or_404(ContractorImport, pk=pk)
        return render(request, 'daily_reports/import_confirm_delete.html', {'ci': ci})

    def post(self, request, pk):
        ci = get_object_or_404(ContractorImport, pk=pk)
        ci.delete()
        messages.success(request, 'Contractor import deleted.')
        return redirect('daily_reports:import_list')


class ImportTemplateDownloadView(LoginRequiredMixin, View):
    def get(self, request):
        wb = build_template_workbook()
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        response = HttpResponse(
            buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = (
            'attachment; filename="contractor_daily_report_template.xlsx"'
        )
        return response
