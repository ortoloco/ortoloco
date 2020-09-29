from django.conf.urls import include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.conf import settings
admin.autodiscover()
from django.contrib.auth.views import LoginView
from django.views.generic import RedirectView
from .views import Custom500View, error, politoloco_profile, beipackzettel_profile, openid_init, date
import juntagrico
from juntagrico.views import home as jhome


import django


#handler500 = Custom500View.as_view()

urlpatterns = [
	url('^500$', Custom500View.as_view()),    
	url('^500/test$',error),
    
    url('^$', jhome),

    url(r'^info/date$', date),
	
    url(r'^politoloco/profile$', politoloco_profile),
    url(r'^beipackzettel/profile$', beipackzettel_profile),

    url(r'^', include('juntagrico.urls')),
    url(r'^impersonate/', include('impersonate.urls')),

    url(r'^accounts/login/$',  LoginView.as_view()),

    url(r'^',include('juntagrico_billing.urls')),
    url(r'^',include('juntagrico_pg.urls')),

    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^openid/', include('oidc_provider.urls', namespace='oidc_provider')),
    url(r'^openidinit$', openid_init),
    url(r'^', include('juntagrico_webdav.urls')),
	
    url(r'^', include('juntagrico_polling.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls)),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),
]
