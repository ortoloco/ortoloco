from axes.models import AccessAttempt, AccessLog
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from ortoloco.tests import OrtolocoTestCase


class AuthenticationTests(TestCase):
    def test_authenticate_without_credentials_and_users_without_member(self):
        # OAuth2TokenMiddleware calls authenticate without credentials. With several users without member
        # juntagrico < 2.1.1 raised MultipleObjectsReturned (production error on /nextcloud/profile)
        User.objects.create_user('orphan_1')
        User.objects.create_user('orphan_2')
        # axes needs a request
        self.assertIsNone(authenticate(request=RequestFactory().get('/nextcloud/profile/')))


class LoginLockoutTests(OrtolocoTestCase):
    """
    django-axes: AXES_FAILURE_LIMIT failed logins lock the combination of user and ip address
    (AXES_LOCKOUT_PARAMETERS), not the whole ip.
    """
    password = 'lockout-test-password'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.victim = cls.create_member('victim@example.org')
        cls.neighbour = cls.create_member('neighbour@example.org')
        for member in (cls.victim, cls.neighbour):
            member.confirmed = True  # ENFORCE_MAIL_CONFIRMATION
            member.save()
            member.user.set_password(cls.password)
            member.user.save()

    def login(self, member, password, ip='203.0.113.7'):
        self.client.logout()
        self.client.post('/accounts/login/', {'username': member.email, 'password': password}, REMOTE_ADDR=ip)
        return '_auth_user_id' in self.client.session

    def lock_out_victim(self):
        for _ in range(settings.AXES_FAILURE_LIMIT):
            self.assertFalse(self.login(self.victim, 'wrong'))

    def test_account_locked_after_failures(self):
        self.lock_out_victim()
        # correct password from the same ip is rejected
        self.assertFalse(self.login(self.victim, self.password))

    def test_other_users_on_same_ip_can_log_in(self):
        self.lock_out_victim()
        self.assertTrue(self.login(self.neighbour, self.password))

    def test_only_failures_recorded(self):
        self.assertTrue(self.login(self.neighbour, self.password))
        self.assertFalse(AccessLog.objects.exists())  # no log of successful logins
        self.assertFalse(self.login(self.victim, 'wrong'))
        self.assertTrue(AccessAttempt.objects.filter(username=self.victim.email).exists())

    def test_same_user_on_other_ip_can_log_in(self):
        self.lock_out_victim()
        self.assertTrue(self.login(self.victim, self.password, ip='198.51.100.23'))
