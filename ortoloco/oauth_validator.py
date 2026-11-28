from oauth2_provider.oauth2_validators import OAuth2Validator


class OrtolocoOAuth2Validator(OAuth2Validator):
    """
    Adds the member data to the OpenID Connect claims, by default there is only `sub` (user id).
    """
    # id: Nextcloud identifies accounts by the member id, not by the user id in `sub`
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope | {'groups': 'groups', 'id': 'member_id'}

    def get_additional_claims(self):
        return {
            'id': lambda request: request.user.member.id,
            'name': lambda request: f'{request.user.member.first_name} {request.user.member.last_name}',
            'given_name': lambda request: request.user.member.first_name,
            'family_name': lambda request: request.user.member.last_name,
            'email': lambda request: request.user.member.email,
            'groups': lambda request: list(request.user.groups.values_list('name', flat=True)),
        }
