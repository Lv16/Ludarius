from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


class TokenFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user, created = User.objects.get_or_create(username='apitest', defaults={'email':'apitest@example.com'})
        if created:
            self.user.set_password('testpass123')
            self.user.save()
        from django.core.cache import cache
        cache.clear()
        self.client = APIClient()

    def test_obtain_refresh_logout_cookie_flow(self):
        # obtain
        r = self.client.post('/api/token/', {'username': 'apitest', 'password': 'testpass123'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.data)
        # refresh token should not be in JSON body
        self.assertNotIn('refresh', r.data)
        # cookie should be set
        self.assertIsNotNone(self.client.cookies.get('refresh_token'))

        # refresh using cookie (no body)
        r2 = self.client.post('/api/token/refresh/', {}, format='json')
        self.assertEqual(r2.status_code, 200)
        self.assertIn('access', r2.data)

        # logout
        r3 = self.client.post('/api/token/logout/', {}, format='json')
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.data.get('detail'), 'Logged out.')

    def test_login_throttle_limits(self):
        # exceed login attempts with wrong password
        for i in range(6):
            r = self.client.post('/api/token/', {'username': 'apitest', 'password': 'wrongpass'}, format='json')
            if i < 5:
                # until limit reached, should be 401 or 400
                self.assertIn(r.status_code, (400, 401))
            else:
                # after limit, expect 429 Too Many Requests
                self.assertEqual(r.status_code, 429)
