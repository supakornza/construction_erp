from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


class DigestTokenAuthentication(BaseAuthentication):
    """Bearer token auth checked against ERP_DIGEST_SECRET env var."""

    def authenticate(self, request):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return None
        token = auth[7:].strip()
        expected = getattr(settings, 'ERP_DIGEST_SECRET', '')
        if not expected or token != expected:
            raise AuthenticationFailed('Invalid digest token.')
        from apps.accounts.models import User
        user = User.objects.filter(is_active=True).order_by('-is_superuser').first()
        if not user:
            raise AuthenticationFailed('No active user found.')
        return (user, None)
