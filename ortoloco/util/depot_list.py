from django.utils import timezone, dateformat
from django.db.models import Count, Q
from django.core.files.storage import default_storage

from juntagrico.config import Config
from juntagrico.dao.depotdao import DepotDao
from juntagrico.dao.listmessagedao import ListMessageDao
from juntagrico.dao.subscriptiondao import SubscriptionDao
from juntagrico.util.pdf import render_to_pdf_storage
from juntagrico.util.temporal import weekdays
from juntagrico.util.subs import activate_future_depots
from juntagrico.entity.subtypes import SubscriptionType
from juntagrico.mailer import adminnotification


def depot_list_generation(*args, **options):
    if not options['force'] and timezone.now().weekday() not in Config.depot_list_generation_days():
        print(
            'not the specified day for depot list generation, use --force to override')
        return

    if options['future'] or timezone.now().weekday() in Config.depot_list_generation_days():
        activate_future_depots()

    if options['force'] and not options['future']:
        print('future depots ignored, use --future to override')

    products = [{'name': 'Gemüse', 'sizes': [{'name': 'Tasche', 'key': 'gmues'}]},
                {'name': 'Obst', 'sizes': [{'name': 'Portion', 'key': 'obst'}]},
                {'name': 'Brot', 'sizes': [{'name': '500g', 'key': 'brot'}]},
                {'name': 'Eier', 'sizes': [{'name': 'Schachtel', 'key': 'eier'}]},
                {'name': 'Tofu', 'sizes': [{'name': 'Portion', 'key': 'tofu'}]}]

    gmues_types = SubscriptionType.objects.filter(pk__in=[6, 7, 8, 9, 10, 11, 12, 13, 18])
    obst_types = SubscriptionType.objects.filter(pk__in=[6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 31])
    brot_types = SubscriptionType.objects.filter(pk__in=[8, 9, 12, 13, 16, 17, 19, 20])
    tofu_types = SubscriptionType.objects.filter(pk__in=[30])
    eier_types = SubscriptionType.objects.filter(pk__in=[23])

    now = dateformat.format(timezone.now(), 'Y-m-d')

    subs = SubscriptionDao.all_active_subscritions(). \
        annotate(gmues=Count('parts',
                             filter=Q(parts__type__in=gmues_types) & Q(
                                 parts__activation_date__lte=now) & (Q(
                                 parts__deactivation_date__isnull=True) | Q(parts__deactivation_date__gt=now)),
                             distinct=True)). \
        annotate(obst=Count('parts',
                            filter=Q(parts__type__in=obst_types) & Q(parts__activation_date__lte=now) & (Q(
                                parts__deactivation_date__isnull=True) | Q(parts__deactivation_date__gt=now)),
                            distinct=True)). \
        annotate(brot=Count('parts',
                            filter=Q(parts__type__in=brot_types) & Q(parts__activation_date__lte=now) & (Q(
                                parts__deactivation_date__isnull=True) | Q(
                                parts__deactivation_date__gt=now)), distinct=True)). \
        annotate(tofu=Count('parts',
                            filter=Q(parts__type__in=tofu_types) & Q(
                                parts__activation_date__lte=now) & (Q(
                                parts__deactivation_date__isnull=True) | Q(parts__deactivation_date__gt=now)),
                            distinct=True)). \
        annotate(eier=Count('parts',
                            filter=Q(parts__type__in=eier_types) & Q(
                                parts__activation_date__lte=now) & (Q(
                                parts__deactivation_date__isnull=True) | Q(parts__deactivation_date__gt=now)),
                            distinct=True))

    depots = DepotDao.all_depots_for_list().order_by('sort_order').prefetch_related('subscription_set'). \
        annotate(
        gmues=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=gmues_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True)). \
        annotate(
        obst=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=obst_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True)). \
        annotate(
        brot=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=brot_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True)). \
        annotate(
        tofu=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=tofu_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True)). \
        annotate(
        eier=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=eier_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True))

    days = DepotDao.all_depots_for_list().prefetch_related('subscription_set'). \
        values('weekday').order_by('weekday'). \
        annotate(
        gmues=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=gmues_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True)). \
        annotate(
        obst=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=obst_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True)). \
        annotate(
        brot=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=brot_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True)). \
        annotate(
        tofu=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=tofu_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True)). \
        annotate(
        eier=Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=eier_types) & Q(
            subscription_set__parts__activation_date__lte=now) & (Q(
            subscription_set__parts__deactivation_date__isnull=True) | Q(
            subscription_set__parts__deactivation_date__gt=now)), distinct=True))

    for day in days:
        day['name'] = weekdays[day['weekday']]

    for product in products:
        for size in product['sizes']:
            total = 0
            for day in days:
                total += day[size['key']]
            size['total'] = total

    depot_dict = {
        'weekdays': days,
        'depots': depots,
        'products': products,
        'subscriptions': subs,
        'messages': ListMessageDao.all_active(),
    }

    render_to_pdf_storage('exports_oooo/depotlist.html',
                          depot_dict, 'depotlist.pdf')
    render_to_pdf_storage('exports_oooo/depot_overview.html',
                          depot_dict, 'depot_overview.pdf')
    render_to_pdf_storage('exports_oooo/amount_overview.html',
                          depot_dict, 'amount_overview.pdf')

    adminnotification.depot_list_generated()

    # cleanup files from preview runs
    legacy_files = ['depotlist_pre.pdf', 'depot_overview_pre.pdf', 'amount_overview_pre.pdf']
    for file in legacy_files:
        if default_storage.exists(file):
            default_storage.delete(file)
