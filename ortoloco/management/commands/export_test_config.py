import datetime
import json
from pathlib import Path

from django.core import serializers
from django.core.management.base import BaseCommand
from django.db.models import Q

from juntagrico.entity.depot import Depot, Tour
from juntagrico.entity.location import Location
from juntagrico.entity.subs import SubscriptionPart
from juntagrico.entity.subtypes import (
    ProductSize, SubscriptionBundle, SubscriptionBundleProductSize, SubscriptionCategory, SubscriptionProduct,
    SubscriptionType,
)

FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'ortoloco_config.json'

# only the depot data that is public anyway (my.ortoloco.ch/signup/external), plus tour and order.
# Not exported: descriptions, access information, contacts, fee, capacity, pickup times.
DEPOT_FIELDS = ['name', 'tour', 'weekday', 'location', 'depot_list', 'visible', 'sort_order']
LOCATION_FIELDS = ['name', 'latitude', 'longitude', 'addr_street', 'addr_zipcode', 'addr_location', 'visible']


def serialize(queryset, fields=None):
    return json.loads(serializers.serialize('json', queryset.order_by('id'), fields=fields))


class Command(BaseCommand):
    help = (
        "Export ortoloco's subscription types, products, tours and depots with their ids as test fixture. "
        "Only exports configuration that is public, no members, subscriptions or contacts."
    )

    def handle(self, *args, **options):
        today = datetime.date.today()
        # visible or still in use by active or waiting subscription parts
        used_type_ids = SubscriptionPart.objects.filter(
            Q(deactivation_date__isnull=True) | Q(deactivation_date__gte=today)
        ).values('type')
        types = SubscriptionType.objects.filter(Q(visible=True) | Q(id__in=used_type_ids))
        bundles = SubscriptionBundle.objects.filter(types__in=types).distinct()
        categories = SubscriptionCategory.objects.filter(bundles__in=bundles).distinct()
        bundle_sizes = SubscriptionBundleProductSize.objects.filter(bundle__in=bundles)
        sizes = ProductSize.objects.filter(id__in=bundle_sizes.values('product_size'))
        products = SubscriptionProduct.objects.filter(id__in=sizes.values('product'))
        # depots on the depot lists, their tours and locations
        depots = Depot.objects.filter(depot_list=True)
        tours = Tour.objects.filter(depots__in=depots).distinct()
        locations = Location.objects.filter(depot__in=depots).distinct()

        objects = [
            *serialize(categories), *serialize(bundles), *serialize(products), *serialize(sizes),
            *serialize(bundle_sizes), *serialize(types), *serialize(tours),
            *serialize(locations, LOCATION_FIELDS), *serialize(depots, DEPOT_FIELDS),
        ]
        FIXTURE.parent.mkdir(exist_ok=True)
        FIXTURE.write_text(json.dumps(objects, indent=2, ensure_ascii=False) + '\n')
        self.stdout.write(
            f'{FIXTURE}: {types.count()} subscription types, {bundles.count()} bundles, {products.count()} products, '
            f'{sizes.count()} sizes, {tours.count()} tours, {depots.count()} depots, {locations.count()} locations'
        )
