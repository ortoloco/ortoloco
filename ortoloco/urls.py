from django.urls import include, path
from django.contrib import admin
import debug_toolbar
from .views import Custom500View, nextcloud_profile
from share_info.views import share_info
from ortoloco import views as ortoloco


urlpatterns = [
    # django
    path('admin/', admin.site.urls),

    # django-debug-toolbar
    path('__debug__/', include(debug_toolbar.urls)),

    # django-oauth-toolkit
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('nextcloud/profile/', nextcloud_profile),

    # django-oidc-provider
    path('openid/', include('oidc_provider.urls', namespace='oidc_provider')),

    # juntagrico
    path('', include('juntagrico.urls')),
    path('impersonate/', include('impersonate.urls')),

    # juntagrico-billing
    path('', include('juntagrico_billing.urls')),

    # juntagrico-postgres
    path('', include('juntagrico_pg.urls')),

    # juntagrico-webdav
    path('', include('juntagrico_webdav.urls')),

    # juntagrico-polling
    path('', include('juntagrico_polling.urls')),

    # juntagrico-contribution
    path('jcr/', include('juntagrico_contribution.urls')),

    # ortoloco custom error page
    path('500', Custom500View.as_view()),

    # ortoloco registration process overwrite
    path('oooosi/info', share_info, name='cs-shares-info'),

    # ortoloco tour list downloads
    path('my/pdf/touroverview', ortoloco.tour_overview, name='lists-depot-touroverview'),
    path('my/pdf/tourlist', ortoloco.tour_list, name='lists-depot-tourlist'),
]
