from django.core.management.base import BaseCommand, CommandError
from apps.projects.models import Project
from apps.project_controls.importers import _import_rap


class Command(BaseCommand):
    help = 'Import Recovery Action Plan items from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help='Path to Recovery Action Plan .xlsx file')
        parser.add_argument('--project', type=str, required=True,
                            help='Project contract_no or pk')
        parser.add_argument('--action', choices=['update', 'skip'], default='update')

    def handle(self, *args, **options):
        filepath = options['filepath']
        project_key = options['project']
        action = options['action']

        try:
            project = Project.objects.get(contract_no=project_key)
        except Project.DoesNotExist:
            try:
                project = Project.objects.get(pk=int(project_key))
            except (Project.DoesNotExist, ValueError):
                raise CommandError(f'Project not found: {project_key}')

        self.stdout.write(f'Importing RAP for: {project.project_name}')
        with open(filepath, 'rb') as f:
            file_content = f.read()

        success, failed, errors = _import_rap(project, file_content, action)
        self.stdout.write(self.style.SUCCESS(f'Done. Items imported: {success}, Failed: {failed}'))
        if errors:
            self.stdout.write(self.style.WARNING(f'Errors: {errors}'))
