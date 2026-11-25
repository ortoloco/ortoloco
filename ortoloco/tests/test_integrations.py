"""
Interfaces used by other systems: changes here break them without notice in my.ortoloco.

- cloud.ortoloco.ch (Nextcloud) logs in with OAuth2 and reads /nextcloud/profile/
- other services log in with OpenID Connect and read /openid/userinfo
- the signup form on www.ortoloco.ch reads and posts /signup/external
"""
import datetime
import json

from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.models import get_access_token_model, get_application_model
from oidc_provider.models import Client, Token

from juntagrico.entity.member import Member

from ortoloco.tests import OrtolocoTestCase


class NextcloudProfileTests(OrtolocoTestCase):
    url = '/nextcloud/profile/'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.member.user.groups.add(Group.objects.create(name='Betriebsgruppe'))
        application = get_application_model().objects.create(
            name='nextcloud',
            client_type='confidential',
            authorization_grant_type='authorization-code',
            redirect_uris='https://cloud.ortoloco.ch/apps/sociallogin/custom_oauth2/my.ortoloco',
        )
        get_access_token_model().objects.create(
            user=cls.member.user, application=application, token='nextcloud-test-token', scope='nextcloud',
            expires=timezone.now() + datetime.timedelta(hours=1),
        )

    def get_profile(self, token='nextcloud-test-token'):
        return self.client.get(self.url, HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_profile(self):
        response = self.get_profile()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'id': self.member.id,
            'email': self.member.email,
            'firstName': self.member.first_name,
            'lastName': self.member.last_name,
            'displayName': f'{self.member.first_name} {self.member.last_name}',
            'roles': ['Betriebsgruppe'],
        })

    def test_profile_with_users_without_member(self):
        # production error 2026-11: users without member broke the token authentication
        User.objects.create_user('orphan_1')
        User.objects.create_user('orphan_2')
        self.assertEqual(self.get_profile().status_code, 200)

    def test_invalid_token(self):
        self.assertEqual(self.get_profile('invalid').status_code, 403)


class OpenIDConnectTests(OrtolocoTestCase):
    url = '/openid/userinfo'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.member.user.groups.add(Group.objects.create(name='Betriebsgruppe'))
        client = Client.objects.create(name='service', client_id='service-client', client_secret='secret')
        Token.objects.create(
            user=cls.member.user, client=client, access_token='oidc-test-token', refresh_token='oidc-refresh',
            expires_at=timezone.now() + datetime.timedelta(hours=1), _scope='openid profile email groups',
            _id_token=json.dumps({'sub': str(cls.member.user.id)}),  # issued with the token on login
        )

    def test_userinfo(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer oidc-test-token')
        self.assertEqual(response.status_code, 200)
        userinfo = json.loads(response.content)
        expected = {
            # ortoloco.oidc_provider_settings.userinfo
            'name': f'{self.member.first_name} {self.member.last_name}',
            'given_name': self.member.first_name,
            'family_name': self.member.last_name,
            'email': self.member.email,
            # ortoloco.oidc_provider_settings.CustomScopeClaims
            'groups': ['Betriebsgruppe'],
        }
        self.assertEqual({key: userinfo.get(key) for key in expected}, expected)
        self.assertEqual(userinfo['sub'], str(self.member.user.id))

    def test_invalid_token(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer invalid')
        self.assertEqual(response.status_code, 401)


class ExternalSignupTests(OrtolocoTestCase):
    """
    The form on www.ortoloco.ch gets depots and subscription types as json and posts the signup,
    which continues in the signup process of my.ortoloco.
    """
    url = '/signup/external'

    def signup_data(self, subscription_type, **kwargs):
        return {
            'first_name': 'Erika',
            'family_name': 'Muster',
            'street': 'Bahnhofstrasse',
            'house_number': '42',
            'postal_code': '8953',
            'city': 'Dietikon',
            'phone': '078 123 45 67',
            'email': 'erika.muster@example.org',
            'comment': 'Ich freue mich',
            'by_laws_accepted': 'True',
            f'subscription_{subscription_type.pk}': 1,
            'depot_id': 14,  # GZ Buchegg
            'start_date': (datetime.date.today() + datetime.timedelta(days=14)).isoformat(),
            'shares': 4,
            'membership': 'True',
        } | kwargs

    def test_details(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        details = json.loads(response.content)
        depot = next(depot for depot in details['depots'] if depot['id'] == 14)
        self.assertEqual(
            set(depot), {'id', 'name', 'visible', 'weekday', 'description', 'location'}
        )
        trial = next(sub for sub in details['subscriptions'] if sub['id'] == self.trial_type.pk)
        self.assertLessEqual(
            {'id', 'name', 'shares', 'required_assignments', 'required_core_assignments', 'price', 'trial_days',
             'description', 'is_extra', 'trial'},
            set(trial),
        )
        self.assertTrue(trial['trial'])

    def test_details_ortoloco_subscriptions(self):
        # the form on www.ortoloco.ch uses the ids of the visible subscription types
        details = json.loads(self.client.get(self.url).content)
        ids = {sub['id'] for sub in details['subscriptions']}
        self.assertLessEqual({*range(6, 18), *range(19, 24), *range(30, 34)}, ids)
        self.assertNotIn(18, ids)  # Gemüseabo: still in use, but not orderable
        trial = next(sub for sub in details['subscriptions'] if sub['id'] == 33)
        self.assertTrue(trial['trial'])

    def assert_continues_signup(self, response):
        # the visitor continues in the signup process of my.ortoloco
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/'), response.url)
        self.assertNotIn(response.url, (reverse('signup') + '?mod', reverse('cs-subscription') + '?mod'))
        self.assertEqual(self.client.get(response.url).status_code, 200)

    def test_signup(self):
        response = self.client.post(self.url, self.signup_data(self.sub_type))
        self.assert_continues_signup(response)
        self.assertFalse(Member.objects.filter(email='erika.muster@example.org').exists())  # created on confirmation

    def test_trial_signup_without_shares(self):
        response = self.client.post(self.url, self.signup_data(self.ortoloco_trial_type, shares=0, membership=''))
        self.assert_continues_signup(response)

    def test_existing_email(self):
        # existing members are sent back to the member form
        response = self.client.post(self.url, self.signup_data(self.sub_type, email=self.member.email))
        self.assertRedirects(response, reverse('signup') + '?mod', fetch_redirect_response=False)
