from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.utils import dateformat, timezone
from juntagrico.config import Config
from juntagrico.dao.depotdao import DepotDao
from juntagrico.dao.listmessagedao import ListMessageDao
from juntagrico.dao.subscriptiondao import SubscriptionDao
from juntagrico.entity.subtypes import SubscriptionType
from juntagrico.entity.listmessage import ListMessage
from juntagrico.mailer import adminnotification
from juntagrico.util.pdf import render_to_pdf_storage
from juntagrico.util.subs import activate_future_depots
from juntagrico.util.temporal import weekdays


def depot_list_generation(*args, **options):
    if not options['force'] and timezone.now().weekday() not in Config.depot_list_generation_days():
        print(
            'not the specified day for depot list generation, use --force to override')
        return

    if options['future'] or timezone.now().weekday() in Config.depot_list_generation_days():
        activate_future_depots()

    if options['force'] and not options['future']:
        print('future depots ignored, use --future to override')

    subscription_type_product_map = getattr(settings, "ORTOLOCO_TYPE_SUBSCRIPTIONS")
    ortoloco_tours = getattr(settings, "ORTOLOCO_TOURS")
    products = getattr(settings, "ORTOLOCO_PRODUCTS")
    recurring_message_config = getattr(settings, "ORTOLOCO_RECURRING_MESSAGES")

    # finding subscription types for product keys
    prod_type_map = {
        key: SubscriptionType.objects.filter(pk__in=sub_type_ids)
        for key, sub_type_ids in subscription_type_product_map.items()
    }

    now = dateformat.format(timezone.now(), 'Y-m-d')
    list_week_date = timezone.localdate() + timezone.timedelta(days=7-timezone.localdate().weekday())

    # annotate all subscriptions with the count of product keys
    subs = SubscriptionDao.all_active_subscritions(). \
        annotate(
            **{key: Count('parts',
                        filter=Q(parts__type__in=sub_type_ids) & Q(
                            parts__activation_date__lte=now) & (Q(
                            parts__deactivation_date__isnull=True) | Q(parts__deactivation_date__gt=now)),
                        distinct=True)
            for key, sub_type_ids in prod_type_map.items()
            })

    # annotate all depots with the count of product keys
    depots = DepotDao.all_depots_for_list().order_by('sort_order').prefetch_related('subscription_set'). \
        annotate(
            **{key: Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=key_types) & Q(
                subscription_set__parts__activation_date__lte=now) & (Q(
                subscription_set__parts__deactivation_date__isnull=True) | Q(
                subscription_set__parts__deactivation_date__gt=now)), distinct=True)
            for key, key_types in prod_type_map.items()
            })

    # annotate the days with the counts of product keys
    days = DepotDao.all_depots_for_list().prefetch_related('subscription_set'). \
        values('weekday').order_by('weekday'). \
        annotate(
            **{key: Count('subscription_set__parts', filter=Q(subscription_set__parts__type__in=key_types) & Q(
                subscription_set__parts__activation_date__lte=now) & (Q(
                subscription_set__parts__deactivation_date__isnull=True) | Q(
                subscription_set__parts__deactivation_date__gt=now)), distinct=True)
            for key, key_types in prod_type_map.items()
            })

    for day in days:
        day['name'] = weekdays[day['weekday']]
        day['date'] = list_week_date + timezone.timedelta(days=day['weekday'])

    # daily tours (as opposed to the logical tours - ortoloco_tours)
    day_tours = [
        {
            # 'id': len(ortoloco_tours)*day_index + index,
            'tour': tour['name'],
            'name': '{} - {}'.format(day['name'], tour['name']),
            'day': day,
            'local': tour['local'],
            'depots': day_tour_depots}
        for day_index, day in enumerate(days)
        for index, tour in enumerate(ortoloco_tours)
        for day_tour_depots in [depots.filter(pk__in=tour['depot_ids'], weekday=day['weekday'])]
        if day_tour_depots
    ]

    # calc totals for tours
    for day_tour in day_tours:
        day_tour.update({
            size['key']: sum(getattr(depot, size['key']) for depot in day_tour['depots'])
            for product in products
            for size in product['sizes']
        })

    for product in products:
        for size in product['sizes']:
            size['total'] = sum(day[size['key']] for day in days)

    # update recurring messages
    actual_config_messages = [
        message_config
        for message_config in recurring_message_config
        if not message_config.get('year') or message_config['year'] == list_week_date.year
    ]
    delivery_calender_week = list_week_date.isocalendar().week
    for message_config in actual_config_messages:
        is_active = delivery_calender_week in message_config['weeks']
        for message in ListMessage.objects.filter(message=message_config['message']):
            if message.active != is_active:
                message.active = is_active
                message.save()

    depot_dict = {
        'subscriptions': subs,
        'products': products,
        'depots': depots,

        'weekdays': days,
        'messages': ListMessageDao.all_active(),

        # ortoloco specific
        'day_tours': day_tours,
        'tours': ortoloco_tours
    }

    render_to_pdf_storage('exports_oooo/depotlist.html',
                          depot_dict, 'depotlist.pdf')
    render_to_pdf_storage('exports_oooo/depot_overview.html',
                          depot_dict, 'depot_overview.pdf')
    render_to_pdf_storage('exports_oooo/amount_overview.html',
                          depot_dict, 'amount_overview.pdf')
    render_to_pdf_storage('exports_oooo/tour_overview.html',
                          depot_dict, 'tour_overview.pdf')
    render_to_pdf_storage('exports_oooo/tour_list.html',
                          depot_dict, 'tour_list.pdf')

    adminnotification.depot_list_generated()

    # cleanup files from preview runs
    legacy_files = ['depotlist_pre.pdf', 'depot_overview_pre.pdf', 'amount_overview_pre.pdf']
    for file in legacy_files:
        if default_storage.exists(file):
            default_storage.delete(file)
