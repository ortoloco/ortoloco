from django.shortcuts import render

from juntagrico.util import sessions
from juntagrico.view_decorators import create_subscription_session

old_init = sessions.CSSessionObject.__init__
old_to_dict = sessions.CSSessionObject.to_dict


def new_init(self):
    old_init(self)
    self.share_info_displayed = False


def new_to_dict(self):
    result = old_to_dict(self)
    result["share_info_displayed"] = self.share_info_displayed
    return result


sessions.CSSessionObject.__init__ = new_init
sessions.CSSessionObject.to_dict = new_to_dict


def new_next_page(self):
    # identify next page, based on what information is still missing
    has_subs = self.subscription_size() > 0
    if not self.subscriptions:
        return 'cs-subscription'
    elif has_subs and not self.depot:
        return 'cs-depot'
    elif has_subs and not self.start_date:
        return 'cs-start'
    elif has_subs and not self.co_members_done:
        return 'cs-co-members'
    elif not getattr(self, 'share_info_displayed', False):
        return 'cs-shares-info'
    elif not self.evaluate_ordered_shares():
        return 'cs-shares'
    return 'cs-summary'


sessions.CSSessionObject.next_page = new_next_page


@create_subscription_session
def share_info(request, cs_session):
    cs_session.share_info_displayed = True
    return render(request, "oooosi/share_info.html", {'next_page': cs_session.next_page()})
