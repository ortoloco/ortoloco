import datetime

from django.contrib.auth.models import Permission

from juntagrico.entity.depot import Depot, Tour
from juntagrico.entity.listmessage import ListMessage
from juntagrico.entity.subtypes import ProductSize, SubscriptionType
from juntagrico.tests import JuntagricoTestCase

# synthetic subscriptions of ortoloco test members: depot id -> subscription type ids (ids of ortoloco_config.json)
ORTOLOCO_SUBSCRIPTIONS = {
    14: [10, 30, 23],  # GZ Buchegg (Tue, Di kleines Auto #3): Vegiabo Getreide, Tofu, Eier
    8: [18],  # Höngg (Tue, Di grosses Auto #1): Gemüseabo, not orderable anymore
    6: [33],  # Fondli (Di): Schnupperabo
    19: [8, 23],  # Kalkbreite (Thu, Do grosses Auto #3): Vollabo Brot, Eier
    15: [22, 31],  # Selnau (Thu, Do kleines Auto #4): Hofabo vegi Getreide, Extraportion Obst
    17: [14, 32],  # Fondli (Do): Hof-Abo Getreide, Extraportion Fleisch
}


class OrtolocoTestCase(JuntagricoTestCase):
    """
    The test data of juntagrico (members, permissions, jobs, special cases), extended with ortoloco's world.

    ortoloco/fixtures/ortoloco_config.json contains ortoloco's real subscription types, products, tours and depots
    with their ids, only public configuration: no members, subscriptions, contacts or access information.
    Update it with `python manage.py export_test_config` from a copy of the production database.

    set_up_ortoloco() adds synthetic members with subscriptions in these depots (ORTOLOCO_SUBSCRIPTIONS).
    The depots of juntagrico's test data are removed from the depot lists, so the lists show ortoloco's depots only.
    """
    fixtures = [*JuntagricoTestCase.fixtures, 'ortoloco_config']
    list_printer_password = 'list-printer-test-password'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.set_up_ortoloco()

    @classmethod
    def set_up_ortoloco(cls):
        # real configuration from the fixture
        cls.ortoloco_trial_type = SubscriptionType.objects.get(pk=33)  # Schnupperabo
        cls.ortoloco_tours = Tour.objects.filter(pk__in=range(1, 7))
        cls.ortoloco_depots = Depot.objects.filter(depot_list=True).exclude(pk__in=[cls.depot.pk, cls.depot2.pk])

        # depot lists with ortoloco's depots and products only
        Depot.objects.filter(pk__in=[cls.depot.pk, cls.depot2.pk]).update(depot_list=False)
        ProductSize.objects.filter(product=cls.sub_product).update(show_on_depot_list=False)

        # synthetic members with subscriptions in ortoloco's depots
        activation_date = datetime.date.today() - datetime.timedelta(days=60)
        cls.locos = {}
        for number, (depot_id, type_ids) in enumerate(ORTOLOCO_SUBSCRIPTIONS.items(), start=1):
            loco = cls.create_member(
                f'loco{number}@example.org', first_name=f'Loco{number}', last_name='Muster', confirmed=True,
            )
            subscription = cls.create_sub(
                Depot.objects.get(pk=depot_id), list(SubscriptionType.objects.filter(pk__in=type_ids)),
                activation_date,
            )
            loco.join_subscription(subscription, True)
            cls.locos[depot_id] = loco

        # area notified by the cron job, see ORTOLOCO_AREA_NOTIFY
        cls.area.name = 'Verteilen'
        cls.area.save()

        # depot list messages switched weekly, see ORTOLOCO_RECURRING_MESSAGES
        cls.message_without_tofu = ListMessage.objects.create(message='OHNE TOFU', active=False)
        cls.message_with_tofu = ListMessage.objects.create(message='MIT TOFU', active=False)

        # account of "Listen Drucken.bat" on the garden computer: may only view the lists
        cls.list_printer = cls.member4
        cls.list_printer.confirmed = True  # ENFORCE_MAIL_CONFIRMATION
        cls.list_printer.save()
        cls.list_printer.user.set_password(cls.list_printer_password)
        cls.list_printer.user.save()
        cls.list_printer.user.user_permissions.add(Permission.objects.get(codename='can_view_lists'))
