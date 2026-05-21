from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('project_manager', 'Project Manager'),
        ('construction_manager', 'Construction Manager'),
        ('office_engineer', 'Office Engineer'),
        ('engineer', 'Engineer'),
        ('site_engineer', 'Site Engineer'),
        ('inspector', 'Inspector'),
        ('quantity_surveyor', 'Quantity Surveyor'),
        ('safety_officer', 'Safety Officer'),
        ('document_controller', 'Document Controller'),
        ('project_coordinator', 'Project Coordinator'),
        ('legal_officer', 'Legal Officer'),
        ('environmental_specialist', 'Environmental Specialist'),
        ('senior_advisor', 'Senior Advisor'),
        ('contractor', 'Contractor'),
        ('owner', 'Owner'),
        ('storekeeper', 'Storekeeper'),
        ('viewer', 'Viewer'),
    ]

    # Roles that can create/edit operational records
    OPERATIONAL_ROLES = {
        'admin', 'project_manager', 'construction_manager', 'office_engineer',
        'engineer', 'site_engineer', 'inspector', 'quantity_surveyor',
        'safety_officer', 'storekeeper', 'environmental_specialist',
        'project_coordinator', 'document_controller', 'contractor',
    }

    # Roles that can access financial/cost data
    FINANCIAL_ROLES = {'admin', 'project_manager', 'construction_manager', 'quantity_surveyor', 'office_engineer'}

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='viewer')
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True)

    class Meta:
        ordering = ['username']

    def get_full_name_or_username(self):
        return self.get_full_name() or self.username

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    def is_approver(self):
        return self.role in ('admin', 'project_manager', 'construction_manager', 'engineer') or self.is_superuser

    def can_access_financial(self):
        return self.is_superuser or self.role in self.FINANCIAL_ROLES

    def can_create_records(self):
        return self.is_superuser or self.role in self.OPERATIONAL_ROLES

    def can_view_boq(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'office_engineer',
            'engineer', 'inspector', 'owner', 'quantity_surveyor',
            'project_coordinator', 'senior_advisor', 'legal_officer', 'viewer'}

    def can_view_safety(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'office_engineer',
            'engineer', 'inspector', 'owner', 'safety_officer', 'site_engineer',
            'environmental_specialist', 'project_coordinator'}

    def can_view_quality(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'office_engineer',
            'engineer', 'inspector', 'owner'}

    def can_view_documents(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'office_engineer',
            'engineer', 'quantity_surveyor', 'document_controller',
            'legal_officer', 'project_coordinator'}

    def can_view_project_controls(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'office_engineer',
            'engineer', 'inspector', 'owner', 'quantity_surveyor',
            'site_engineer', 'project_coordinator', 'senior_advisor'}

    def can_view_procurement(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'quantity_surveyor', 'office_engineer'}

    def can_view_hr(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'office_engineer',
            'quantity_surveyor', 'project_coordinator', 'site_engineer'}

    def can_view_change_orders(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'office_engineer',
            'engineer', 'quantity_surveyor', 'legal_officer', 'owner',
            'senior_advisor', 'project_coordinator', 'viewer'}

    def can_view_maintenance(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'office_engineer',
            'engineer', 'site_engineer', 'inspector', 'storekeeper', 'project_coordinator'}

    def can_view_executive_desk(self):
        return self.is_superuser or self.role in {
            'admin', 'project_manager', 'construction_manager', 'owner', 'senior_advisor'}

    def is_contractor(self):
        return self.role == 'contractor'

    def is_owner(self):
        return self.role == 'owner'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.CharField(max_length=200, blank=True)
    position = models.CharField(max_length=100, blank=True)
    signature = models.ImageField(upload_to='signatures/', blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
