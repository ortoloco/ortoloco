from django.conf.urls import include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.conf import settings
admin.autodiscover()
from django.contrib.auth.views import LoginView
from django.views.generic import RedirectView
from static_ortoloco import views as static_ortoloco
from .views import Custom500View, error, politoloco_profile, beipackzettel_profile
import juntagrico
from juntagrico.views import home as jhome


import django


#handler500 = Custom500View.as_view()

urlpatterns = [
	url('^500$', Custom500View.as_view()),    
	url('^500/test$',error),
    
    url('^$', jhome),

    url(r'^politoloco/profile$', politoloco_profile),
    url(r'^beipackzettel/profile$', beipackzettel_profile),

    url(r'^', include('juntagrico.urls')),
    url(r'^impersonate/', include('impersonate.urls')), 
    url(r'^photologue/', include('photologue.urls')),

    url(r'^accounts/login/$',  LoginView.as_view()),

    url(r'^',include('juntagrico_bookkeeping.urls')),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    
    #url('^test_filters/$', my_ortoloco.test_filters),
    #url('^test_filters_post/$', my_ortoloco.test_filters_post),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls)),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),
    #(r'^tinymce/', include('tinymce.urls')),
    #url(r'^medias/(?P<path>.*)$', django.views.static.serve, {
    #    'document_root': settings.MEDIA_ROOT,
    #}),
	#url(r'^downloads/(?P<param>.*)$', RedirectView.as_view(url='/medias/downloads/%(param)s')),
    #url(r'^static/(?P<path>.*)$', django.views.static.serve, {
    #   'document_root': settings.STATIC_ROOT,
    #})
    
    
]
