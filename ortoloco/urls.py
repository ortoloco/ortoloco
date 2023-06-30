from django.urls import include, re_path
from django.urls import path

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()
from django.contrib.auth.views import LoginView
from .views import Custom500View, error, politoloco_profile, beipackzettel_profile, date
from juntagrico.views import home as jhome
from share_info.views import share_info
import debug_toolbar
from ortoloco import views as ortoloco

urlpatterns = [
    re_path('^500$', Custom500View.as_view()),
    re_path('^500/test$', error),

    re_path('^$', jhome),

    re_path(r'^info/date$', date),

    re_path(r'^oooosi/info$', share_info, name='cs-shares-info'),

    re_path(r'^politoloco/profile$', politoloco_profile),
    re_path(r'^beipackzettel/profile$', beipackzettel_profile),

    re_path(r'^', include('juntagrico.urls')),
    re_path(r'^impersonate/', include('impersonate.urls')),

    re_path(r'^accounts/login/$', LoginView.as_view()),

    re_path(r'^', include('juntagrico_billing.urls')),
    re_path(r'^', include('juntagrico_pg.urls')),

    re_path(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    re_path(r'^openid/', include('oidc_provider.urls', namespace='oidc_provider')),

    re_path(r'^', include('juntagrico_webdav.urls')),

    re_path(r'^', include('juntagrico_polling.urls')),

    re_path(r'^admin/', admin.site.urls),
    re_path('__debug__/', include(debug_toolbar.urls)),

    path('my/pdf/touroverview', ortoloco.tour_overview, name='lists-depot-touroverview'),
]
