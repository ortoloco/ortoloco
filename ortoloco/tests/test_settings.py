"""
Settings that have to be maintained every year.
The GitHub workflow runs weekly, so a failing test here is noticed in time.
"""
import datetime

from django.conf import settings
from django.test import SimpleTestCase

# the data of the next year must exist this long before the year starts
ADVANCE = datetime.timedelta(days=31)


def required_years(today):
    """
    :return: years that must be configured on this day: the current one and, one month before new year, the next one
    """
    return {today.year, (today + ADVANCE).year}


def message_names(year):
    return {message['message'] for message in settings.ORTOLOCO_RECURRING_MESSAGES if message.get('year') == year}


class RecurringMessagesTests(SimpleTestCase):
    """
    ORTOLOCO_RECURRING_MESSAGES switches the depot list messages (with or without tofu) per calendar week.
    The entries are defined per year: without the entries of a year, the messages are not switched anymore.
    """
    all_names = {message['message'] for message in settings.ORTOLOCO_RECURRING_MESSAGES}

    def assert_years_configured(self, today):
        for year in sorted(required_years(today)):
            with self.subTest(year=year):
                missing = self.all_names - message_names(year)
                self.assertFalse(
                    missing,
                    f'ORTOLOCO_RECURRING_MESSAGES has no entries {missing} for {year}: add them in settings.py'
                )

    def test_years_configured(self):
        self.assert_years_configured(datetime.date.today())

    def test_required_years(self):
        self.assertEqual(required_years(datetime.date(2026, 11, 30)), {2026})
        self.assertEqual(required_years(datetime.date(2026, 12, 1)), {2026, 2027})
        self.assertEqual(required_years(datetime.date(2027, 1, 1)), {2027})

    def test_weeks_not_overlapping(self):
        # a week must not be with and without tofu at the same time
        for year in {message['year'] for message in settings.ORTOLOCO_RECURRING_MESSAGES if message.get('year')}:
            with self.subTest(year=year):
                weeks = [set(message['weeks']) for message in settings.ORTOLOCO_RECURRING_MESSAGES if message.get('year') == year]
                overlap = set.intersection(*weeks) if len(weeks) > 1 else set()
                self.assertFalse(overlap, f'weeks of {year} with several messages: {sorted(overlap)}')
