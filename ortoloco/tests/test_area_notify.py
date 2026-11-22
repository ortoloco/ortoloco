"""
The cron job on the server calls `python manage.py upcoming_jobs` without arguments: every area in
ORTOLOCO_AREA_NOTIFY gets an email with the participants of its jobs in N days.
These tests replay that call with the real settings.
"""
import datetime

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from juntagrico.entity.jobs import JobType, RecuringJob
from juntagrico.util.temporal import weekdays

from ortoloco.tests import OrtolocoTestCase

AREA, DAYS = 'Verteilen', settings.ORTOLOCO_AREA_NOTIFY['Verteilen']


def job_time(days):
    day = timezone.localdate() + datetime.timedelta(days=days)
    return timezone.make_aware(datetime.datetime.combine(day, datetime.time(10)))


class UpcomingJobsCronTests(OrtolocoTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # job of the area in DAYS days with two participants,
        # both have one past job in this area (past_job of the juntagrico test data)
        cls.upcoming_job = RecuringJob.objects.create(slots=3, time=job_time(DAYS), type=cls.job_type)
        cls.create_assignment(cls.upcoming_job, cls.member)
        cls.create_assignment(cls.upcoming_job, cls.member3)

    def run_cron(self):
        mail.outbox = []
        call_command('upcoming_jobs')

    def test_notification(self):
        self.run_cron()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        job_date = self.upcoming_job.time.date()
        self.assertIn(f'{AREA} - {weekdays[job_date.isoweekday()]} {job_date}', email.subject)
        self.assertEqual(email.to, self.area.get_emails())
        for member in (self.member, self.member3):
            with self.subTest(member=member):
                self.assertIn(f'{member.first_name} {member.last_name} <{member.email}>', email.body)
                # experience: number of past jobs in this area
                self.assertIn(f'{member.first_name} {member.last_name} (1)', email.body)
        self.assertIn(self.job_type.name, email.body)

    def test_no_notification_without_jobs(self):
        self.upcoming_job.time = job_time(DAYS - 1)
        self.upcoming_job.save()
        self.run_cron()
        self.assertEqual(mail.outbox, [])

    def test_only_jobs_on_the_configured_day(self):
        self.upcoming_job.time = job_time(DAYS + 1)
        self.upcoming_job.save()
        self.run_cron()
        self.assertEqual(mail.outbox, [])

    def test_jobs_of_a_day_in_one_email(self):
        other_type = JobType.objects.create(
            name='other type', activityarea=self.area, location=self.job_type.location, default_duration=2
        )
        other_job = RecuringJob.objects.create(slots=1, time=job_time(DAYS) + datetime.timedelta(hours=4), type=other_type)
        self.create_assignment(other_job, self.member2)
        self.run_cron()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('other type', mail.outbox[0].body)
        self.assertIn(self.member2.email, mail.outbox[0].body)

    def test_other_areas_not_notified(self):
        job = RecuringJob.objects.create(slots=1, time=job_time(DAYS), type=self.job_type2)
        self.create_assignment(job, self.member2)
        self.run_cron()
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(self.member2.email, mail.outbox[0].body)

    def test_area_option(self):
        # manual call for a single area
        mail.outbox = []
        call_command('upcoming_jobs', area=AREA, days=DAYS)
        self.assertEqual(len(mail.outbox), 1)
