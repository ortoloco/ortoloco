from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase


class AuthenticationTests(TestCase):
    def test_authenticate_without_credentials_and_users_without_member(self):
        # OAuth2TokenMiddleware calls authenticate without credentials. With several users without member
        # juntagrico < 2.1.1 raised MultipleObjectsReturned (production error on /nextcloud/profile)
        User.objects.create_user('orphan_1')
        User.objects.create_user('orphan_2')
        # axes needs a request
        self.assertIsNone(authenticate(request=RequestFactory().get('/nextcloud/profile/')))
