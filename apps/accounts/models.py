from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('project_manager', 'Project Manager'),
        ('site_engineer', 'Site Engineer'),
        ('quantity_surveyor', 'Quantity Surveyor'),
        ('safety_officer', 'Safety Officer'),
        ('storekeeper', 'Storekeeper'),
        ('viewer', 'Viewer'),
    ]
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
        return self.role in ('admin', 'project_manager') or self.is_superuser


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.CharField(max_length=200, blank=True)
    position = models.CharField(max_length=100, blank=True)
    signature = models.ImageField(upload_to='signatures/', blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
