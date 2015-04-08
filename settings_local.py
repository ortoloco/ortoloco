import os
from ortoloco.settings import *

# Load Credentials
# EMAIL Information
# Database Information
from credentials import *

# I had difficulties with STATIC URL
# ended up to create a symbolic link in :
# in directory: /var/www/site/meine.gartenkooperative.li/gartenkooperative/static
# lrwxrwxrwx 1 sacha sacha   70 Apr  8 22:56 admin -> ../venv/lib/python2.7/site-packages/django/contrib/admin/static/admin/

# STATIC_URL = '/static/tosomeotherurl/'

LOGGING = {
}


