from django.core.management.base import BaseCommand
from django.db import transaction


# PMC/TA Consortium Group – Land Reclamation org chart
ORG_USERS = [
    # (username, first_name, last_name, role, position, is_staff)
    # ── Senior Management ──────────────────────────────────────────
    ('arnon_k',      'Arnon',      'K.',         'project_manager', 'Senior Advisor',          False),
    ('chaiwat_p',    'Chaiwat',    'P.',         'project_manager', 'Project Manager',          True),
    # ── Engineering Team at HQ ─────────────────────────────────────
    ('meererk_p',    'Meererk',    'P.',         'engineer',        'Geotechnical Engineer',   False),
    ('kittipong_t',  'Kittipong',  'T.',         'engineer',        'Senior Coastal Engineer', False),
    ('sorawit_r',    'Sorawit',    'R.',         'admin',           'Contract & Legal Officer', True),
    ('yongyai_m',    'Yongyai',    'M.',         'engineer',        'Environmental Specialist', False),
    # ── Construction Management ────────────────────────────────────
    ('thanut_b',     'Thanut',     'B.',         'project_manager', 'Construction Manager',    False),
    ('jidapha_s',    'Jidapha',    'S.',         'safety_officer',  'Safety Supervisor',       False),
    ('jirawat_n',    'Jirawat',    'N.',         'inspector',       'Site Inspector',          False),
    ('jariyaporn_s', 'Jariyaporn', 'S.',         'inspector',       'Site Inspector',          False),
    # ── Support and Coordination ───────────────────────────────────
    ('bhakapong_b',  'Bhakapong',  'B.',         'project_manager', 'Project Coordinator',     False),
    ('supakorn_p',   'Supakorn',   'P.',         'quantity_surveyor', 'Office Engineer & QS',  False),
    ('patthira_k',   'Patthira',   'K.',         'viewer',          'Secretary / Doc. Control', False),
]

DEFAULT_PASSWORD = 'PMC@2024!'
COMPANY = 'TA Consortium Group'


class Command(BaseCommand):
    help = 'Seed PMC/TA org-chart users (13 people) with roles and profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-passwords',
            action='store_true',
            help='Reset passwords for existing users to the default',
        )

    def handle(self, *args, **options):
        from apps.accounts.models import User, UserProfile

        self.stdout.write(self.style.HTTP_INFO('\nSeeding PMC org-chart users...'))
        created = 0
        updated = 0

        with transaction.atomic():
            for username, first, last, role, position, is_staff in ORG_USERS:
                user, was_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first,
                        'last_name': last,
                        'email': f'{username}@pmc.consultant',
                        'role': role,
                        'is_staff': is_staff,
                        'is_superuser': (role == 'admin'),
                    },
                )

                if was_created:
                    user.set_password(DEFAULT_PASSWORD)
                    user.save()
                    created += 1
                    self.stdout.write(f'  [+] Created  {username:20s}  role={role}')
                else:
                    # Update role/position in case it changed
                    changed = False
                    if user.role != role:
                        user.role = role
                        changed = True
                    if options['reset_passwords']:
                        user.set_password(DEFAULT_PASSWORD)
                        changed = True
                    if changed:
                        user.save()
                        updated += 1
                        self.stdout.write(f'  [~] Updated  {username:20s}  role={role}')
                    else:
                        self.stdout.write(f'  [=] Exists   {username:20s}  role={role}')

                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'company': COMPANY, 'position': position},
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {created}  Updated: {updated}'
        ))
        self.stdout.write('')
        self.stdout.write('Role summary:')
        self.stdout.write(f'  admin            – sorawit_r')
        self.stdout.write(f'  project_manager  – arnon_k, chaiwat_p, thanut_b, bhakapong_b')
        self.stdout.write(f'  engineer         – meererk_p, kittipong_t, yongyai_m')
        self.stdout.write(f'  inspector        – jirawat_n, jariyaporn_s')
        self.stdout.write(f'  safety_officer   – jidapha_s')
        self.stdout.write(f'  quantity_surveyor– supakorn_p')
        self.stdout.write(f'  viewer           – patthira_k')
        self.stdout.write('')
        self.stdout.write(f'Default password : {DEFAULT_PASSWORD}')
        self.stdout.write('  (use --reset-passwords to reset existing accounts)')
