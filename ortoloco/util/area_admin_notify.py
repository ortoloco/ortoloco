import itertools
import collections
from django.utils import timezone
from juntagrico.mailer import EmailSender, get_email_content, base_dict, organisation_subject
from juntagrico.util.temporal import weekdays

from juntagrico.dao.activityareadao import ActivityAreaDao
from juntagrico.dao.jobtypedao import JobTypeDao
from juntagrico.entity.jobs import RecuringJob, Assignment

def notify_upcoming_jobs(*args, **options):

    def job_date(job):
        return job.time.date()
        
    now = timezone.now()
    job__min_date = now + timezone.timedelta(days=options["days"])
    job__min_date = timezone.datetime.combine(job__min_date.date(), timezone.datetime.min.time(), job__min_date.tzinfo)
    job__max_date = job__min_date + timezone.timedelta(days=1)
    job_stats_min_date = now - timezone.timedelta(days=365)

    for area in ActivityAreaDao.all_visible_areas().filter(name=options["area"]):

        job_type_ids = [
            job_type.pk
            for job_type in JobTypeDao.types_by_area(area.pk)
            ]

        # find the jobs for the area in the given day
        for job_date, job_list in itertools.groupby(
            sorted(
                RecuringJob.objects.filter(type__id__in=job_type_ids, time__lte=job__max_date, time__gte=job__min_date),
                key=job_date),
            key=job_date):

            job_list = list(job_list)
            members = [
                member
                for job in job_list
                for member in job.participants
            ]

            assignment_count = collections.Counter([
                assignment.member
                for assignment in Assignment.objects.filter(
                    member__in=members).filter(
                    job__time__lte=now,
                    job__time__gte=job_stats_min_date)
                if assignment.job.type.id in job_type_ids
            ])

            for member in members:
                member.job_count = assignment_count[member]

            d = {'area': area, 'job_date': job_date, 'job_weekday': weekdays[job_date.isoweekday()], 'members': members, 'jobs': job_list}

            # print(get_email_content('j_notify', base_dict(d)))
            EmailSender.get_sender(
                organisation_subject("{area.name} - {job_weekday} {job_date}".format(**d)),
                get_email_content('j_notify', base_dict(d)),
                to=[area.coordinator.email]
            ).send()
