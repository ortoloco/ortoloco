"""
Render the pages, lists and emails that ortoloco customizes, using the test data of juntagrico.
"""
import datetime
import tempfile
from unittest import mock

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from juntagrico.entity.share import Share
from juntagrico.mailer import base_dict, get_email_content
from juntagrico.util import pdf

from ortoloco.tests import OrtolocoTestCase


class PageTests(OrtolocoTestCase):
    def test_home_menu(self):
        response = self.assertGet(reverse('home'))
        self.assertContains(response, 'https://forum.ortoloco.ch/')

    @override_settings(VELO_CODE='9876')
    def test_velo_code_for_active_subscription(self):
        self.assertContains(self.assertGet(reverse('home')), 'Velo Code: 9876')

    @override_settings(VELO_CODE='9876')
    def test_velo_code_hidden_without_active_subscription(self):
        # member2 only has a waiting subscription
        self.assertNotContains(self.assertGet(reverse('home'), member=self.member2), '9876')

    @override_settings(VELO_CODE=None)
    def test_velo_code_hidden_if_not_set(self):
        self.assertNotContains(self.assertGet(reverse('home')), 'Velo Code')

    @mock.patch('ortoloco.templatetags.ortoloco_common.get_news_posts', return_value='<p>ortoloco news</p>')
    def test_areas(self, get_news_posts):
        response = self.assertGet(reverse('areas'))
        self.assertContains(response, 'Kernbereich')  # ortoloco area intro
        # the news embedding is commented out
        self.assertNotContains(response, 'ortoloco news')
        get_news_posts.assert_not_called()

    def test_signup_intro(self):
        self.client.logout()
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'Schnupperabo:')
        self.assertContains(response, 'Regulärer Beitritt:')

    def test_share_intro(self):
        response = self.assertGet(reverse('membership-create'))
        self.assertContains(response, 'CHF 250 pro')


class DepotListTests(OrtolocoTestCase):
    def test_generate_depot_lists(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(pdf, 'internal_storage', FileSystemStorage(location=directory)):
            call_command('generate_depot_list', force=True, future=True)
            storage = pdf.internal_storage
            for name in ('touroverview', 'tourlist', 'depotlist', 'depotoverview', 'amountoverview'):
                with self.subTest(list=name):
                    self.assertTrue(storage.exists(name + '.pdf'))

    def assert_tofu_messages(self, generation_date, without_tofu):
        # the lists are generated for the week after generation_date
        settings.DEPOT_LISTS['touroverview']['extra_context']({'date': generation_date})
        self.message_without_tofu.refresh_from_db()
        self.message_with_tofu.refresh_from_db()
        self.assertEqual(self.message_without_tofu.active, without_tofu)
        self.assertEqual(self.message_with_tofu.active, not without_tofu)

    def test_recurring_messages(self):
        # ORTOLOCO_RECURRING_MESSAGES: tofu is delivered every two weeks
        self.assert_tofu_messages(datetime.date(2026, 11, 18), without_tofu=False)  # week 48 of 2026
        self.assert_tofu_messages(datetime.date(2026, 11, 25), without_tofu=True)  # week 49 of 2026
        self.assert_tofu_messages(datetime.date(2026, 12, 30), without_tofu=False)  # week 1 of 2027


class EmailTests(OrtolocoTestCase):
    def test_share_created(self):
        shares = [Share.objects.create(member=self.member, value=250), Share.objects.create(member=self.member, value=250)]
        content = get_email_content('s_created', base_dict({'shares': shares, 'member': self.member}))
        self.assertIn('2 Anteilscheine zu je CHF 250 bestellt', content)
        self.assertIn('Gesamtbetrag von CHF 500', content)

    def test_area_jobs_contacts(self):
        content = get_email_content('j_notify', base_dict({
            'area': self.area, 'job_date': '01.01.2027', 'job_weekday': 'Freitag', 'members': [], 'jobs': [],
        }))
        self.assertTrue(content.strip())
