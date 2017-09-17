from django.conf.urls import include, url



urlpatterns = [
	url('^$', redirect_away),
	
]

def redirect(request_away):
    """
    redirects to my google if you enter by heroku live link whatever
    """
    return redirect("http://www.google.ch")