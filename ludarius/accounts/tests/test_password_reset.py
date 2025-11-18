from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.test import APIClient


class PasswordResetTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user, created = User.objects.get_or_create(username='resetuser', defaults={'email':'reset@example.com'})
        if created:
            self.user.set_password('origpass')
            self.user.save()
        from django.core.cache import cache
        cache.clear()
        self.client = APIClient()

    def test_password_reset_request_returns_200(self):
        r = self.client.post('/api/accounts/password-reset/', {'email': 'no-such@example.com'}, format='json')
        self.assertEqual(r.status_code, 200)
        r2 = self.client.post('/api/accounts/password-reset/', {'email': 'reset@example.com'}, format='json')
        self.assertEqual(r2.status_code, 200)

    def test_password_reset_get_redirects_to_frontend(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        r = self.client.get(f'/api/accounts/password-reset/confirm/?uid={uid}&token={token}')
        # should be a redirect
        self.assertIn(r.status_code, (301, 302))
        self.assertIn('http://', r['Location'])

    def test_password_reset_rate_limit(self):
        # clear cache and perform multiple requests
        from django.core.cache import cache
        cache.clear()
        for i in range(4):
            r = self.client.post('/api/accounts/password-reset/', {'email': 'reset@example.com'}, format='json')
            if i < 3:
                self.assertEqual(r.status_code, 200)
            else:
                self.assertEqual(r.status_code, 429)

    def test_password_reset_confirm_changes_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        r = self.client.post('/api/accounts/password-reset/confirm/', {'uid': uid, 'token': token, 'new_password': 'newpass123'}, format='json')
        self.assertEqual(r.status_code, 200)
        # reload user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(username='resetuser')
        self.assertTrue(user.check_password('newpass123'))
