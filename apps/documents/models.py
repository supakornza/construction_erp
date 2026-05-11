from django.db import models
from apps.accounts.models import User
from apps.projects.models import Project


class DocumentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = 'Document Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    STATUS_CHOICES = [
        ('Current', 'Current'),
        ('Superseded', 'Superseded'),
        ('Void', 'Void'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    document_no = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    category = models.ForeignKey(DocumentCategory, on_delete=models.PROTECT)
    revision = models.CharField(max_length=10, default='0')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Current')
    file = models.FileField(upload_to='documents/%Y/%m/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        unique_together = ('project', 'document_no', 'revision')

    def __str__(self):
        return f"{self.document_no} Rev.{self.revision} – {self.title}"


class DocumentRevision(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='revisions')
    revision_no = models.CharField(max_length=10)
    change_description = models.TextField()
    revised_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    revised_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='documents/revisions/%Y/%m/', blank=True)

    class Meta:
        ordering = ['-revised_at']

    def __str__(self):
        return f"{self.document} – Rev {self.revision_no}"
