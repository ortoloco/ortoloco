"""
Content of the generated documents. The tests render the html that is converted to pdf.
"""
import datetime
import re

from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from juntagrico.config import Config
from juntagrico.entity.listmessage import ListMessage
from juntagrico.entity.share import Share
from juntagrico.util.depot_list import depot_list_data

from ortoloco.tests import OrtolocoTestCase


def text(html):
    html = re.sub(r'<style>.*?</style>', '', html, flags=re.DOTALL)
    return re.sub(r'\s+', ' ', strip_tags(html))


class DepotListContentTests(OrtolocoTestCase):
    """
    Lists of the next delivery days with ortoloco's depots, tours and products and the synthetic subscriptions
    of ORTOLOCO_SUBSCRIPTIONS. The expected numbers follow from the products of the subscription types.
    Product columns: Gemüse (Tasche), Obst (Portion), Brot (500 g), Eier (Schachtel), Tofu (Portion).
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        ListMessage.objects.create(message='Bitte Taschen zurückbringen', active=True)
        # rendered once for all tests of this class, the tests only read the text
        context = depot_list_data()
        cls.lists = {
            depot_list['file_name']: text(render_to_string(depot_list['template'], context | depot_list['extra_context']))
            for depot_list in Config.depot_lists(context=context)
        }

    def depot_page(self, depotlist, depot_name):
        # text of the page of one depot on the depot list
        pages = depotlist.split('Depotliste: ')[1:]
        return next(page for page in pages if re.search(rf'\d{{4}} {re.escape(depot_name)} ', page))

    def test_depot_list(self):
        depotlist = self.lists['depotlist']
        self.assertIn('Bitte Taschen zurückbringen', depotlist)
        for product in ('Gemüse', 'Obst', 'Brot', 'Eier', 'Tofu'):
            with self.subTest(product=product):
                self.assertIn(product, depotlist)

        # tour and position of the depot in the tour, see snippet_depotlist_header.html
        buchegg = self.depot_page(depotlist, 'GZ Buchegg')
        self.assertIn('Dienstag', buchegg)
        self.assertIn('Tour: Di kleines Auto (Renault) #3', buchegg)
        # Vegiabo Getreide, Tofu, Eier
        self.assertIn('Total: 1 1 0 1 1', buchegg)
        self.assertIn('Loco1 Muster 1 1 1 1', buchegg)
        self.assertNotIn('Loco4', buchegg)

        kalkbreite = self.depot_page(depotlist, 'Kalkbreite')
        self.assertIn('Donnerstag', kalkbreite)
        self.assertIn('Tour: Do grosses Auto (Opel) #3', kalkbreite)
        self.assertIn('Total: 1 1 1 1 0', kalkbreite)  # Vollabo Brot, Eier

        # no tour on the depot list for the depots on the farm
        fondli = self.depot_page(depotlist, 'Fondli (Di)')
        self.assertNotIn('Tour:', fondli)
        self.assertIn('Loco3 Muster', fondli)  # Schnupperabo

    def test_tour_overview(self):
        # tour, position and depot for each delivery day
        touroverview = self.lists['touroverview']
        self.assertIn(
            'Dienstag Tour Reihe Depot Di Fondli #1 Fondli (Di) Di kleines Auto (Renault) #1 Hunzikerareal '
            'Di kleines Auto (Renault) #2 GZ Oerlikon Di kleines Auto (Renault) #3 GZ Buchegg '
            'Di kleines Auto (Renault) #4 Kraftwerk1 Di grosses Auto (Opel) #1 Höngg', touroverview
        )
        self.assertIn(
            'Do grosses Auto (Opel) #1 ABZ Herrlig Do grosses Auto (Opel) #2 Stadtgärtnerei (ex-Zirkusareal) '
            'Do grosses Auto (Opel) #3 Kalkbreite', touroverview
        )

    def test_depot_overview(self):
        depotoverview = self.lists['depotoverview']
        self.assertIn('GZ Buchegg 1 1 0 1 1', depotoverview)
        self.assertIn('Höngg 1 0 0 0 0', depotoverview)  # Gemüseabo
        self.assertIn('Selnau 0 2 0 0 0', depotoverview)  # Hofabo vegi, Extraportion Obst
        self.assertIn('Hunzikerareal 0 0 0 0 0', depotoverview)
        self.assertIn('Total 3 2 0 1 1', depotoverview)  # Tuesday
        self.assertIn('Total 1 4 1 1 0', depotoverview)  # Thursday

    def test_amount_overview(self):
        # subscriptions and amounts per day and tour
        amountoverview = self.lists['amountoverview']
        self.assertIn('Dienstag 3 3 2 0 1 1', amountoverview)
        self.assertIn('Donnerstag 3 1 4 1 1 0', amountoverview)
        self.assertIn('Gesamt 6 4 6 1 2 1', amountoverview)
        self.assertIn('Di kleines Auto (Renault) 1 1 1 0 1 1', amountoverview)
        self.assertIn('Do kleines Auto (Renault) 1 0 2 0 0 0', amountoverview)

    def test_tour_list(self):
        tourlist = self.lists['tourlist']
        self.assertIn('Di kleines Auto (Renault): Dienstag', tourlist)
        self.assertIn('Do grosses Auto (Opel): Donnerstag', tourlist)
        self.assertIn('Di kleines Auto (Renault) 1 1 0 1 1', tourlist)


class ShareCertificateTests(OrtolocoTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.year = datetime.date.today().year - 1
        for _ in range(2):
            Share.objects.create(member=cls.member, value=250, paid_date=datetime.date(cls.year, 3, 1))

    def test_certificate(self):
        response = self.assertGet(reverse('share-certificate') + f'?year={self.year}')
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_certificate_content(self):
        shares = self.member.active_shares_for_date(date=datetime.date(self.year, 12, 31))
        certificate = text(render_to_string('exports/share_certificate.html', {
            'member': self.member,
            'cert_date': datetime.date.today(),
            'shares_date': datetime.date(self.year, 12, 31),
            'shares': [{'value': 250, 'count': shares.count(), 'total': 500}],
            'shares_total': 500,
        }))
        # ortoloco wording instead of the member vocabulary
        self.assertIn(f'Genossenschafter:in-Nr.: {self.member.id}', certificate)
        self.assertIn('CHF 250', certificate)
        self.assertIn('Total: CHF 500', certificate)
