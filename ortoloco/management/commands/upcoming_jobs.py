from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string



class Command(BaseCommand):

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '--area',
            help='area name for which to send the notification',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='how many days in the future should the jobs be',
        )

    # entry point used by manage.py
    def handle(self, *args, **options):
        for generator in ['ortoloco.util.area_admin_notify.notify_upcoming_jobs']:
            gen = import_string(generator)
            gen(*args, **options)

