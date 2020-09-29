from django.utils.translation import ugettext as _
from oidc_provider.lib.claims import ScopeClaims


def userinfo(claims, user):
    member = user.member
    claims['name'] = '{0} {1}'.format(member.first_name, member.last_name)
    claims['given_name'] = member.first_name
    claims['family_name'] = member.last_name
    claims['email'] = member.email

    return claims


class CustomScopeClaims(ScopeClaims):

    info_groups = (
        _(u'Groups'),
        _(u'Group memberships in juntagrico'),
    )

    def scope_groups(self):
        # self.user - Django user instance.
        # self.userinfo - Dict returned by OIDC_USERINFO function.
        # self.scopes - List of scopes requested.
        # self.client - Client requesting this claims.
        membergroups = self.user.groups.values_list('name', flat=True)
        grouplist = list(membergroups)
        dic = {
            'groups': grouplist,
        }

        return dic
