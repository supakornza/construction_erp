from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAdminOrReadOnly, IsProjectMember
from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer
from apps.daily_reports.models import DailyReport
from apps.daily_reports.serializers import DailyReportSerializer
from apps.manpower.models import DailyManpowerRecord
from apps.manpower.serializers import DailyManpowerRecordSerializer
from apps.equipment.models import DailyEquipmentRecord
from apps.equipment.serializers import DailyEquipmentRecordSerializer
from apps.materials.models import MaterialDelivery, Material
from apps.materials.serializers import MaterialDeliverySerializer
from apps.boq.models import BOQItem, DailyProgressRecord
from apps.boq.serializers import BOQItemSerializer, DailyProgressRecordSerializer
from apps.safety.models import SafetyInspection
from apps.safety.serializers import SafetyInspectionSerializer
from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    search_fields = ['project_name', 'contract_no']

    def perform_destroy(self, instance):
        if not (self.request.user.is_superuser or self.request.user.role == 'admin'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only admins can delete projects.')
        instance.delete()


class DailyReportViewSet(viewsets.ModelViewSet):
    queryset = DailyReport.objects.all().select_related('project', 'prepared_by')
    serializer_class = DailyReportSerializer
    permission_classes = [IsProjectMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'status', 'report_date']

    def perform_destroy(self, instance):
        if not (self.request.user.is_superuser or self.request.user.role == 'admin'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only admins can delete reports.')
        instance.delete()


class ManpowerRecordViewSet(viewsets.ModelViewSet):
    queryset = DailyManpowerRecord.objects.all()
    serializer_class = DailyManpowerRecordSerializer
    permission_classes = [IsProjectMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'report_date', 'category']


class EquipmentRecordViewSet(viewsets.ModelViewSet):
    queryset = DailyEquipmentRecord.objects.all()
    serializer_class = DailyEquipmentRecordSerializer
    permission_classes = [IsProjectMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'report_date', 'status']


class MaterialDeliveryViewSet(viewsets.ModelViewSet):
    queryset = MaterialDelivery.objects.all()
    serializer_class = MaterialDeliverySerializer
    permission_classes = [IsProjectMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'material', 'delivery_date']


class MaterialStockViewSet(viewsets.ViewSet):
    permission_classes = [IsProjectMember]

    def list(self, request):
        from apps.materials.models import get_stock_balance
        from apps.projects.models import Project
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({'error': 'project_id is required'}, status=400)
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=404)
        materials = Material.objects.all()
        result = []
        for mat in materials:
            bal = get_stock_balance(project, mat)
            if bal['delivered'] > 0 or bal['used'] > 0:
                result.append({
                    'material_id': mat.id,
                    'material_name': mat.name,
                    'unit': mat.unit,
                    **{k: float(v) for k, v in bal.items()},
                })
        return Response(result)


class BOQItemViewSet(viewsets.ModelViewSet):
    queryset = BOQItem.objects.all()
    serializer_class = BOQItemSerializer
    permission_classes = [IsProjectMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project']


class BOQProgressViewSet(viewsets.ModelViewSet):
    queryset = DailyProgressRecord.objects.all()
    serializer_class = DailyProgressRecordSerializer
    permission_classes = [IsProjectMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'boq_item', 'record_date']


class SafetyInspectionViewSet(viewsets.ModelViewSet):
    queryset = SafetyInspection.objects.all()
    serializer_class = SafetyInspectionSerializer
    permission_classes = [IsProjectMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'status']


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsProjectMember]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'status', 'category']


class DashboardChartDataViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        from apps.dashboard.views import DashboardChartDataView
        view = DashboardChartDataView()
        view.request = request
        return view.get(request)
