from django.conf.urls import include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from django.contrib.auth.views import LoginView
from .views import Custom500View, error, politoloco_profile, beipackzettel_profile, date
from juntagrico.views import home as jhome
from share_info.views import share_info
import debug_toolbar
from django.urls import include, path

urlpatterns = [
	url('^500$', Custom500View.as_view()),    
	url('^500/test$',error),
    
    url('^$', jhome),

    url(r'^info/date$', date),

    url(r'^oooosi/info$', share_info, name='cs-shares-info'),
	
    url(r'^politoloco/profile$', politoloco_profile),
    url(r'^beipackzettel/profile$', beipackzettel_profile),

    url(r'^', include('juntagrico.urls')),
    url(r'^impersonate/', include('impersonate.urls')),

    url(r'^accounts/login/$',  LoginView.as_view()),

    url(r'^',include('juntagrico_billing.urls')),
    url(r'^',include('juntagrico_pg.urls')),

    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^openid/', include('oidc_provider.urls', namespace='oidc_provider')),

    url(r'^', include('juntagrico_webdav.urls')),
	
    url(r'^', include('juntagrico_polling.urls')),

    url(r'^admin/', admin.site.urls),
    path('__debug__/', include(debug_toolbar.urls)),
]
	
]
