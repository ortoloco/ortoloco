from juntagrico.util.auth import AuthenticateWithEmail


class SafeAuthenticateWithEmail(AuthenticateWithEmail):
    """
    juntagrico's backend queries users with username=None when called without
    credentials (e.g. by OAuth2TokenMiddleware), which matches every user
    without a member and raises MultipleObjectsReturned.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        return super().authenticate(request, username, password, **kwargs)
