"""
Login of other services with my.ortoloco, replayed as the services do it. See docs/login-clients.md.

- Nextcloud (cloud.ortoloco.ch): OAuth2 with django-oauth-toolkit, profile and groups from /nextcloud/profile/
- WordPress instances: OpenID Connect with the plugin "OpenID Connect Generic Client" and django-oauth-toolkit (/o/)
"""
import json
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import Client as TestClient
from jwcrypto import jwk, jwt
from oauth2_provider.models import get_application_model

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
    scope = 'nextcloud'

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
            'redirect_uri': self.redirect_uri, 'state': 'nextcloud-state',
            **({'scope': self.scope} if self.scope else {}),
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

    def test_login_without_scope(self):
        self.scope = None
        token = self.get_token(self.authorize())
        self.assertEqual(token['scope'], 'nextcloud')
        response = self.client.get('/nextcloud/profile/', HTTP_AUTHORIZATION=f'Bearer {token["access_token"]}')
        self.assertEqual(response.status_code, 200)

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

    def test_userinfo_instead_of_profile(self):
        # possible replacement of /nextcloud/profile/: same account ids, as Social Login (OAuth2) uses "id" before "sub"
        self.application.algorithm = self.application.RS256_ALGORITHM
        self.application.save()
        self.scope = 'openid profile email groups member_id'
        # member id and user id must differ to notice a mix-up
        User.objects.create_user('without_member')
        member = self.create_member('other@example.org')
        member.user.groups.add(Group.objects.get(name='Betriebsgruppe'))
        self.assertNotEqual(member.pk, member.user.pk)
        self.client.force_login(member.user)

        token = self.get_token(self.authorize())
        header = {'HTTP_AUTHORIZATION': f'Bearer {token["access_token"]}'}
        # scope nextcloud is only needed for the profile
        self.assertEqual(self.client.get('/nextcloud/profile/', **header).status_code, 403)
        userinfo = self.client.get('/o/userinfo/', **header).json()
        self.assertEqual(userinfo['id'], member.pk)
        self.assertEqual(userinfo['sub'], str(member.user.pk))
        self.assertEqual(userinfo['email'], member.email)
        self.assertEqual(userinfo['name'], f'{member.first_name} {member.last_name}')
        self.assertEqual(userinfo['groups'], ['Betriebsgruppe'])

    def test_token_for_profile_only(self):
        # an access token must not log in on other pages: services could act as their users
        token = self.get_token(self.authorize())
        header = {'HTTP_AUTHORIZATION': f'Bearer {token["access_token"]}'}
        self.assertEqual(self.client.get('/nextcloud/profile/', **header).status_code, 200)
        self.assertEqual(self.client.get('/my/profile', **header).status_code, 302)
        self.assertEqual(self.client.get('/admin/', **header).status_code, 302)
        self.client.post('/accounts/login/', {'username': 'x', 'password': 'x'}, **header)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_token(self):
        self.client.logout()
        self.assertEqual(
            self.client.get('/nextcloud/profile/', HTTP_AUTHORIZATION='Bearer invalid').status_code, 403)
        self.assertEqual(self.client.get('/nextcloud/profile/').status_code, 403)

    def test_unknown_redirect_uri(self):
        response = self.client.get('/o/authorize/', {
            'response_type': 'code', 'client_id': self.application.client_id,
            'redirect_uri': 'https://evil.example.org/', 'scope': 'nextcloud',
        })
        self.assertNotEqual(response.status_code, 302)


class WordPressOpenIDConnectTests(LoginClientTestCase):
    """
    WordPress plugin "OpenID Connect Generic Client" (daggerhart-openid-connect-generic) with django-oauth-toolkit.
    Application in the admin as in docs/login-clients.md.
    """
    redirect_uri = 'https://wptest.ortoloco.ch/wp-admin/admin-ajax.php?action=openid-connect-authorize'
    client_id = 'wordpress-test-client'
    client_secret = 'wordpress-test-secret'
    post_logout_redirect_uri = 'https://wptest.ortoloco.ch/'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Application = get_application_model()
        application = Application(
            name='wptest', client_id=cls.client_id, client_secret=cls.client_secret, hash_client_secret=True,
            redirect_uris=cls.redirect_uri, post_logout_redirect_uris=cls.post_logout_redirect_uri,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            skip_authorization=True, algorithm=Application.RS256_ALGORITHM,
        )
        application.full_clean()
        application.save()

    def login(self, scope='openid email profile', **params):
        response = self.client.get('/o/authorize/', {
            'response_type': 'code', 'client_id': self.client_id, 'redirect_uri': self.redirect_uri,
            'scope': scope, 'state': 'wp-state', **params,
        })
        # no consent page, directly back to WordPress
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith(self.redirect_uri), response['Location'])
        params = query(response['Location'])
        self.assertEqual(params['state'], 'wp-state')
        self.client.logout()  # the token request comes from the WordPress server
        response = self.token(params['code'])
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def token(self, code, secret=None):
        return self.client.post('/o/token/', {
            'grant_type': 'authorization_code', 'code': code, 'redirect_uri': self.redirect_uri,
            'client_id': self.client_id, 'client_secret': secret or self.client_secret,
        })

    def userinfo(self, tokens, url='/o/userinfo/'):
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def verified_id_token(self, tokens):
        # as WordPress: signature with the key from the jwks endpoint, issuer and audience
        keys = jwk.JWKSet.from_json(self.client.get('/o/.well-known/jwks.json').content.decode())
        id_token = jwt.JWT(
            jwt=tokens['id_token'], key=keys, algs=['RS256'], expected_type='JWS',
            check_claims={'iss': f'{SITE}/o', 'aud': self.client_id, 'exp': None},
        )
        self.assertEqual(id_token.token.jose_header['alg'], 'RS256')
        return json.loads(id_token.claims)

    def test_discovery(self):
        config = self.client.get('/o/.well-known/openid-configuration').json()
        self.assertEqual(config['issuer'], f'{SITE}/o')
        self.assertEqual(config['authorization_endpoint'], f'{SITE}/o/authorize/')
        self.assertEqual(config['token_endpoint'], f'{SITE}/o/token/')
        self.assertEqual(config['userinfo_endpoint'], f'{SITE}/o/userinfo/')
        self.assertEqual(config['jwks_uri'], f'{SITE}/o/.well-known/jwks.json')
        self.assertEqual(config['end_session_endpoint'], f'{SITE}/o/logout/')

    def test_login(self):
        id_token = self.verified_id_token(self.login(nonce='wp-nonce'))
        self.assertEqual(id_token['nonce'], 'wp-nonce')
        self.assertEqual(id_token['sub'], str(self.member.user.id))
        self.assertEqual(id_token['email'], self.member.email)
        # only with the scopes "groups" and "member_id"
        self.assertNotIn('groups', id_token)
        self.assertNotIn('id', id_token)

    def test_userinfo(self):
        # WordPress recognizes accounts by sub (user id) and fills in the user with these claims
        self.assertEqual(self.userinfo(self.login('openid email profile groups')), {
            'sub': str(self.member.user.id),
            'name': f'{self.member.first_name} {self.member.last_name}',
            'given_name': self.member.first_name,
            'family_name': self.member.last_name,
            'email': self.member.email,
            'groups': ['Betriebsgruppe'],
        })

    def test_groups_in_id_token(self):
        # Nextcloud Social Login reads the groups of OpenID Connect providers from the id token
        id_token = self.verified_id_token(self.login('openid email profile groups'))
        self.assertEqual(id_token['groups'], ['Betriebsgruppe'])

    def test_token_is_no_login(self):
        tokens = self.login()
        header = {'HTTP_AUTHORIZATION': f'Bearer {tokens["access_token"]}'}
        for url, code in (('/my/profile', 302), ('/admin/', 302), ('/nextcloud/profile/', 403)):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url, **header).status_code, code)

    def test_wrong_secret(self):
        response = self.client.get('/o/authorize/', {
            'response_type': 'code', 'client_id': self.client_id, 'redirect_uri': self.redirect_uri, 'scope': 'openid',
        })
        self.client.logout()
        self.assertEqual(self.token(query(response['Location'])['code'], 'wrong').status_code, 401)

    def test_logout(self):
        tokens = self.login()
        self.client.force_login(self.member.user)
        response = self.client.get('/o/logout/', {
            'id_token_hint': tokens['id_token'], 'post_logout_redirect_uri': self.post_logout_redirect_uri,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.post_logout_redirect_uri)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_unknown_redirect(self):
        tokens = self.login()
        response = self.client.get('/o/logout/', {
            'id_token_hint': tokens['id_token'], 'post_logout_redirect_uri': 'https://evil.example.org/',
        })
        self.assertEqual(response.status_code, 400)

    def test_logout_page_needs_post(self):
        # /logout/ of juntagrico (django) only logs out with POST: a link or redirect to it fails with 405,
        # therefore WordPress must use /o/logout/ as end session endpoint
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
