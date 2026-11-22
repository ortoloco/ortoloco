"""
Login of other services with my.ortoloco, replayed as the services do it. See docs/login-clients.md.

- Nextcloud (cloud.ortoloco.ch): OAuth2 with django-oauth-toolkit, profile and groups from /nextcloud/profile/
- WordPress instances: OpenID Connect with django-oidc-provider and the plugin "OpenID Connect Client"
"""
import json
from urllib.parse import parse_qs, urlparse

import jwt
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client as TestClient
from oauth2_provider.models import get_application_model
from oidc_provider.models import Client, ResponseType

from ortoloco.tests import OrtolocoTestCase

HOST = 'my.ortoloco.ch'
SITE = f'https://{HOST}'


def query(url):
    return {key: values[0] for key, values in parse_qs(urlparse(url).query).items()}


class HttpsClient(TestClient):
    # requests via https like in production
    def generic(self, *args, **kwargs):
        kwargs['secure'] = True
        return super().generic(*args, **kwargs)


class LoginClientTestCase(OrtolocoTestCase):
    client_class = HttpsClient

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.member.user.groups.add(Group.objects.create(name='Betriebsgruppe'))

    def setUp(self):
        self.client.defaults['HTTP_HOST'] = HOST
        self.client.force_login(self.member.user)


class NextcloudLoginTests(LoginClientTestCase):
    """
    Nextcloud app "Social Login", custom OAuth2 provider "my.ortoloco".
    Application in the admin as in docs/login-clients.md.
    """
    redirect_uri = 'https://cloud.ortoloco.ch/apps/sociallogin/custom_oauth2/my.ortoloco'
    client_secret = 'nextcloud-test-secret'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Application = get_application_model()
        cls.application = Application.objects.create(
            name='nextcloud',
            client_id='nextcloud-test-client',
            client_secret=cls.client_secret,
            hash_client_secret=True,
            user=cls.admin.user,
            redirect_uris='https://cloud.ortoloco.ch/index.php/apps/sociallogin/custom_oauth2/my.ortoloco '
                          + cls.redirect_uri,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            skip_authorization=True,
            algorithm=Application.NO_ALGORITHM,
        )

    def authorize(self):
        # without PKCE (code_challenge), like Social Login
        response = self.client.get('/o/authorize/', {
            'response_type': 'code', 'client_id': self.application.client_id,
            'redirect_uri': self.redirect_uri, 'scope': 'nextcloud', 'state': 'nextcloud-state',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(self.redirect_uri), response.url)
        params = query(response.url)
        self.assertEqual(params['state'], 'nextcloud-state')
        return params['code']

    def get_token(self, code):
        self.client.logout()  # the token request comes from the Nextcloud server
        response = self.client.post('/o/token/', {
            'grant_type': 'authorization_code', 'code': code, 'redirect_uri': self.redirect_uri,
            'client_id': self.application.client_id, 'client_secret': self.client_secret,
        })
        self.assertEqual(response.status_code, 200, response.content)
        return json.loads(response.content)

    def test_login(self):
        token = self.get_token(self.authorize())
        self.assertEqual(token['scope'], 'nextcloud')
        response = self.client.get('/nextcloud/profile/', HTTP_AUTHORIZATION=f'Bearer {token["access_token"]}')
        self.assertEqual(response.status_code, 200)
        profile = json.loads(response.content)
        self.assertEqual(profile['email'], self.member.email)
        self.assertEqual(profile['displayName'], f'{self.member.first_name} {self.member.last_name}')
        # Nextcloud maps the groups from "roles"
        self.assertEqual(profile['roles'], ['Betriebsgruppe'])

    def test_pkce_not_required(self):
        # Social Login does not send a code_challenge: PKCE_REQUIRED (default True) must stay False
        self.assertIs(settings.OAUTH2_PROVIDER['PKCE_REQUIRED'], False)

    def test_wrong_secret(self):
        code = self.authorize()
        self.client.logout()
        response = self.client.post('/o/token/', {
            'grant_type': 'authorization_code', 'code': code, 'redirect_uri': self.redirect_uri,
            'client_id': self.application.client_id, 'client_secret': 'wrong',
        })
        self.assertEqual(response.status_code, 401)

    def test_unknown_redirect_uri(self):
        response = self.client.get('/o/authorize/', {
            'response_type': 'code', 'client_id': self.application.client_id,
            'redirect_uri': 'https://evil.example.org/', 'scope': 'nextcloud',
        })
        self.assertNotEqual(response.status_code, 302)


class WordPressOpenIDConnectTests(LoginClientTestCase):
    """
    WordPress plugin "OpenID Connect Client" (daggerhart-openid-connect-generic).
    Client in the admin as in docs/login-clients.md.
    """
    redirect_uri = 'https://wptest.ortoloco.ch/wp-admin/admin-ajax.php?action=openid-connect-authorize'
    client_secret = 'wordpress-test-secret'
    post_logout_redirect_uri = 'https://wptest.ortoloco.ch/'
    scope = 'openid email profile'  # setting of the plugin

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        call_command('creatersakey')  # done once on the server
        cls.oidc_client = Client.objects.create(
            name='wptest', client_id='wordpress-test-client', client_secret=cls.client_secret,
            client_type='confidential', jwt_alg='RS256', require_consent=False, reuse_consent=True,
            _redirect_uris=cls.redirect_uri, _post_logout_redirect_uris=cls.post_logout_redirect_uri,
        )
        cls.oidc_client.response_types.add(ResponseType.objects.get(value='code'))

    def test_discovery(self):
        # endpoints configured in the plugin
        response = self.client.get('/openid/.well-known/openid-configuration')
        self.assertEqual(response.status_code, 200)
        config = json.loads(response.content)
        self.assertEqual(config['issuer'], f'{SITE}/openid')
        self.assertEqual(config['authorization_endpoint'], f'{SITE}/openid/authorize')
        self.assertEqual(config['token_endpoint'], f'{SITE}/openid/token')
        self.assertEqual(config['userinfo_endpoint'], f'{SITE}/openid/userinfo')
        self.assertEqual(config['jwks_uri'], f'{SITE}/openid/jwks')

    def authorize(self):
        response = self.client.get('/openid/authorize', {
            'response_type': 'code', 'client_id': self.oidc_client.client_id,
            'redirect_uri': self.redirect_uri, 'scope': self.scope, 'state': 'wp-state',
        })
        # require_consent=False: no consent page, directly back to WordPress
        self.assertEqual(response.status_code, 302)
        location = response['Location']
        self.assertTrue(location.startswith(self.redirect_uri.split('?')[0]), location)
        params = query(location)
        self.assertEqual(params['state'], 'wp-state')
        return params['code']

    def get_tokens(self, code):
        self.client.logout()  # the token request comes from the WordPress server
        response = self.client.post('/openid/token', {
            'grant_type': 'authorization_code', 'code': code, 'redirect_uri': self.redirect_uri,
            'client_id': self.oidc_client.client_id, 'client_secret': self.client_secret,
        })
        self.assertEqual(response.status_code, 200, response.content)
        return json.loads(response.content)

    def test_login(self):
        tokens = self.get_tokens(self.authorize())

        # id token signed with RS256, verifiable with the keys of the jwks endpoint
        jwks = jwt.PyJWKSet.from_json(self.client.get('/openid/jwks').content.decode())
        header = jwt.get_unverified_header(tokens['id_token'])
        self.assertEqual(header['alg'], 'RS256')
        key = next(key for key in jwks.keys if key.key_id == header['kid'])
        id_token = jwt.decode(
            tokens['id_token'], key=key, algorithms=['RS256'], audience=self.oidc_client.client_id, issuer=f'{SITE}/openid',
        )
        self.assertEqual(id_token['sub'], str(self.member.user.id))

        # user info of the plugin scopes
        response = self.client.get('/openid/userinfo', HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
        self.assertEqual(response.status_code, 200)
        userinfo = json.loads(response.content)
        self.assertEqual(userinfo['sub'], id_token['sub'])
        self.assertEqual(userinfo['email'], self.member.email)
        self.assertEqual(userinfo['given_name'], self.member.first_name)
        self.assertEqual(userinfo['family_name'], self.member.last_name)
        self.assertEqual(userinfo['name'], f'{self.member.first_name} {self.member.last_name}')

    def test_groups_scope(self):
        # groups are only sent if a client requests the scope "groups"
        self.scope = 'openid email profile groups'
        tokens = self.get_tokens(self.authorize())
        response = self.client.get('/openid/userinfo', HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
        self.assertEqual(json.loads(response.content)['groups'], ['Betriebsgruppe'])

    def test_wrong_secret(self):
        code = self.authorize()
        self.client.logout()
        response = self.client.post('/openid/token', {
            'grant_type': 'authorization_code', 'code': code, 'redirect_uri': self.redirect_uri,
            'client_id': self.oidc_client.client_id, 'client_secret': 'wrong',
        })
        self.assertEqual(response.status_code, 400)

    def test_end_session(self):
        # logout in WordPress also logs out of my.ortoloco and returns to WordPress
        tokens = self.get_tokens(self.authorize())
        self.client.force_login(self.member.user)
        response = self.client.get('/openid/end-session', {
            'id_token_hint': tokens['id_token'], 'post_logout_redirect_uri': self.post_logout_redirect_uri,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.post_logout_redirect_uri)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_page_needs_post(self):
        # /logout/ of juntagrico (django) only logs out with POST: a link or redirect to it fails with 405,
        # therefore WordPress must use /openid/end-session as end session endpoint
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
