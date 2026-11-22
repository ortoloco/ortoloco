from impersonate.helpers import User, check_allow_for_user
from impersonate.middleware import ImpersonateMiddleware

ADMIN_PATH = '/admin/'


class AdminImpersonateMiddleware(ImpersonateMiddleware):
    """
    django-impersonate does not impersonate on URI_EXCLUSIONS (default ^admin/) for every impersonator.
    Superusers also impersonate in the admin, e.g. to check what a staff member sees there.
    All other checks of django-impersonate (allowed users, MAX_DURATION, read only) still apply.
    """
    def process_request(self, request):
        response = super().process_request(request)
        if response is not None or request.impersonator is not None:
            return response
        real_user = request.user
        if (
            '_impersonate' in request.session
            and request.path.startswith(ADMIN_PATH)
            and real_user.is_authenticated
            and real_user.is_superuser
        ):
            new_user = User.objects.filter(pk=request.session['_impersonate']).first()
            if new_user is not None and check_allow_for_user(request, new_user):
                request.impersonator = request.real_user = real_user
                request.user = new_user
                new_user.is_impersonate = True
                new_user.impersonator = real_user
        return response
