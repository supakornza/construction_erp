from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class DashboardQualityIntegrationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='dashboard-quality',
            password='pw',
            role='admin',
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_dashboard_loads_without_quality_data(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/index.html')
        self.assertIn('quality_metrics', response.context)
        self.assertEqual(response.context['quality_metrics']['ncr_open'], 0)
