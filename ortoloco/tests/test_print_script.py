"""
"Listen Drucken.bat" on the garden computer logs in with curl and downloads the depot lists to print them.
It cannot be changed easily, so these tests replay what it does. If one fails, the printing in the garden breaks.

The script does:
    1. GET  /accounts/login/                    -> read the csrftoken cookie
    2. POST /accounts/login/                    -> fields csrfmiddlewaretoken, username (email), password
    3. GET  each url of PRINT_SCRIPT_URLS       -> save the response as pdf and print it
"""
import tempfile
from unittest import mock

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.test import Client

from juntagrico.util import pdf

from ortoloco.tests import OrtolocoTestCase

LOGIN_URL = '/accounts/login/'

# urls downloaded by the script (juntagrico's lists-download), keep in sync with "Listen Drucken.bat"
PRINT_SCRIPT_URLS = [
    '/list/depotlist',
    '/list/amountoverview',
    '/list/depotoverview',
    '/list/touroverview',
]


class PrintScriptTests(OrtolocoTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        patcher = mock.patch.object(pdf, 'internal_storage', FileSystemStorage(location=self.directory.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        # curl does not send csrf headers, so check the token like in production
        self.curl = Client(enforce_csrf_checks=True)

    def login(self):
        self.curl.get(LOGIN_URL)
        token = self.curl.cookies[settings.CSRF_COOKIE_NAME].value
        return self.curl.post(LOGIN_URL, {
            'csrfmiddlewaretoken': token,
            'username': self.list_printer.email,
            'password': self.list_printer_password,
        }, HTTP_REFERER='https://my.ortoloco.ch' + LOGIN_URL)

    def test_login(self):
        response = self.login()
        self.assertEqual(response.status_code, 302, 'login of the print script failed')
        self.assertIn('_auth_user_id', self.curl.session)

    def test_lists_are_configured(self):
        # the url names are the keys of DEPOT_LISTS
        for url in PRINT_SCRIPT_URLS:
            with self.subTest(url=url):
                self.assertIn(url.rsplit('/', 1)[1], settings.DEPOT_LISTS)

    def test_download_lists(self):
        call_command('generate_depot_list', force=True, future=True)
        self.login()
        for url in PRINT_SCRIPT_URLS:
            with self.subTest(url=url):
                response = self.curl.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], 'application/pdf')
                self.assertTrue(response.content.startswith(b'%PDF'), 'the script would print something else than a pdf')

    def test_download_requires_login(self):
        # redirected to the login before the file is read, no lists needed
        for url in PRINT_SCRIPT_URLS:
            with self.subTest(url=url):
                self.assertEqual(self.curl.get(url).status_code, 302)
