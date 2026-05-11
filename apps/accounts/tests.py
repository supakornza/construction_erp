from django.test import TestCase, Client
from django.urls import reverse
from .models import User


class UserAuthTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='testadmin', password='testpass123', role='admin'
        )
        self.viewer = User.objects.create_user(
            username='testviewer', password='testpass123', role='viewer'
        )

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testadmin', 'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('dashboard:index'))

    def test_login_failure(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testadmin', 'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)

    def test_role_assignment(self):
        self.assertEqual(self.admin.role, 'admin')
        self.assertTrue(self.admin.is_admin())
        self.assertTrue(self.admin.is_approver())

    def test_viewer_not_admin(self):
        self.assertFalse(self.viewer.is_admin())
        self.assertFalse(self.viewer.is_approver())

    def test_user_list_requires_admin(self):
        self.client.login(username='testviewer', password='testpass123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_user_list(self):
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)
