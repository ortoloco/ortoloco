# Django settings for ortoloco project.
import os

"""
    General Settings
"""
DEBUG = os.environ.get("ORTOLOCO_DEBUG", "True") == "True"

ALLOWED_HOSTS = ['.orto.xiala.net', '.ortoloco.ch', 'localhost', 'ortoloco-dev.herokuapp.com']

SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

ROOT_URLCONF = 'ortoloco.urls'

SITE_ID = 1

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'ortoloco.wsgi.application'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'd3w=vyfqpqmcj#&ge1d0$ch#ff7$qt#6z)lzqt=9pg8wg%d^%s'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'ortoloco/templates'
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'juntagrico.personalisation.loaders.personal_directories.Loader'
            ],
            'debug' : True
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'subdomains.middleware.SubdomainURLRoutingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'impersonate.middleware.ImpersonateMiddleware'
)

INSTALLED_APPS = (
    'juntagrico',
    'static_ortoloco',
    'photologue',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'tinymce',
    'impersonate',
    'storages'
)


"""
    Email Settings
"""
WHITELIST_EMAILS = []
def whitelist_email_from_env(var_env_name):
    email = os.environ.get(var_env_name)
    if email:
        WHITELIST_EMAILS.append(email.replace('@gmail.com', '(\+\S+)?@gmail.com'))

whitelist_email_from_env("ORTOLOCO_EMAIL_USER")

if DEBUG is True:
    for key in list(os.environ.keys()):
        if key.startswith("ORTOLOCO_EMAIL_WHITELISTED"):
            whitelist_email_from_env(key)


EMAIL_HOST = os.environ.get('ORTOLOCO_EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('ORTOLOCO_EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('ORTOLOCO_EMAIL_PASSWORD')
EMAIL_PORT = os.environ.get('ORTOLOCO_EMAIL_PORT', 587)
EMAIL_USE_TLS = os.environ.get('ORTOLOCO_EMAIL_TLS', True)

"""
    Admin Settings
"""
ADMINS = (
    ('Admin', os.environ.get('ORTOLOCO_ADMIN_EMAIL')),
)
MANAGERS = ADMINS
SERVER_EMAIL="server@ortoloco.ch"

"""
    Auth Settings
"""
AUTHENTICATION_BACKENDS = (
    'juntagrico.util.auth.AuthenticateWithEmail',
    'django.contrib.auth.backends.ModelBackend'
)

"""
    DB Settings
"""
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('ORTOLOCO_DATABASE_ENGINE'), # 'django.db.backends.postgresql_psycopg2', #'django.db.backends.sqlite3'
        'NAME': os.environ.get('ORTOLOCO_DATABASE_NAME'), # 'db.sqlite',                      # Or path to database file if using sqlite3.
        'USER': os.environ.get('ORTOLOCO_DATABASE_USER'), # The following settings are not used with sqlite3:
        'PASSWORD': os.environ.get('ORTOLOCO_DATABASE_PASSWORD'),
        'HOST': os.environ.get('ORTOLOCO_DATABASE_HOST'),# Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': os.environ.get('ORTOLOCO_DATABASE_PORT', False),  # Set to empty string for default.
    }
}

"""
    Localization Settings
"""
TIME_ZONE = 'Europe/Zurich'

LANGUAGE_CODE = 'de_CH'

USE_I18N = True

USE_L10N = True

DATE_INPUT_FORMATS =['%d.%m.%Y',]

USE_TZ = True


"""
    Static Settings
"""
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_URL = '/static/'

STATICFILES_DIRS = ( 
    os.path.join(BASE_DIR, 'static_general'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)


"""
    File & Storage Settings
"""
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

DEFAULT_FILE_STORAGE = 'ortoloco.utils.MediaS3BotoStorage'

try:
    AWS_ACCESS_KEY_ID = os.environ['ORTOLOCO_AWS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['ORTOLOCO_AWS_KEY']
    AWS_STORAGE_BUCKET_NAME = os.environ['ORTOLOCO_AWS_BUCKET_NAME']
except KeyError:
    raise KeyError('Need to define AWS environment variables: ' +
                   'ORTOLOCO_AWS_KEY_ID, ORTOLOCO_AWS_KEY, and ORTOLOCO_AWS_BUCKET_NAME')

# Default Django Storage API behavior - don't overwrite files with same name
AWS_S3_FILE_OVERWRITE = False

MEDIA_ROOT = 'media'

MEDIA_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME

"""
    TINYMCE Settings
"""
TINYMCE_JS_URL = '/static/external/tinymce/tinymce.min.js'

TINYMCE_DEFAULT_CONFIG = {
    'theme': "modern",
    'plugins': 'link',
    'relative_urls': False,
    'valid_styles': {
        '*': 'color,text-align,font-size,font-weight,font-style,text-decoration'
    },
    'menu': {
        'edit': {
            'title': 'Edit',
            'items': 'undo redo | cut copy paste | selectall'
        },
        'insert': {
            'title': 'Insert',
            'items': 'link'
        },
        'format': {
            'title': 'Format',
            'items': 'bold italic underline strikethrough superscript subscript | formats | removeformat'
        }
    }
}

"""
    Impersonate Settings
"""
IMPERSONATE_REDIRECT_URL = "/my/profile"

"""
    Logging Settings
"""
# logging config - copied from here: http://stackoverflow.com/questions/18920428/django-logging-on-heroku
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
                       'pathname=%(pathname)s lineno=%(lineno)s ' +
                       'funcname=%(funcName)s %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'null': {
            'level': 'INFO',
            'class': 'logging.NullHandler',
            },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

"""
    Subdomain Settings
"""
# A dictionary of urlconf module paths, keyed by their subdomain.
SUBDOMAIN_URLCONFS = {
    None: 'ortoloco.urls', 
    'www': 'ortoloco.urls',
    'my': 'ortoloco.myurlsredirect',
    'ortoloco': 'fuckoff'
}

"""
    Photologue Settings
"""
PHOTOLOGUE_GALLERY_SAMPLE_SIZE = 3

"""
    Juntagrico Settings
"""
MEMBER_STRING = "Loco"
MEMBERS_STRING = "Locos"
ASSIGNMENT_STRING = "Böhnli"
ASSIGNMENTS_STRING = "Böhnlis"
ORGANISATION_NAME = "ortoloco"
ORGANISATION_LONG_NAME = "Genossenschaft ortoloco – Die regionale Gartenkooperative"
ORGANISATION_ADDRESS = {"name":"ortoloco",
            "street" : "Albisriederstr.",
            "number" : "203b",
            "zip" : "8047 ",
            "city" : "Zürich",
            "extra" : ""}
ORGANISATION_BANK_CONNECTION = {"PC" : "85-199010-5",
            "IBAN" : "CH72 0900 0000 8519 9010 5",
            "BIC" : "POFICHBEXXX",
            "NAME" : "Postfinance",
            "ESR" : "01-123-45"}
INFO_EMAIL = "info@ortoloco.ch"
SERVER_URL = "www.ortoloco.ch"
ADMINPORTAL_NAME = "my.ortoloco"
ADMINPORTAL_SERVER_URL = "www.ortoloco.ch"
BUSINESS_REGULATIONS = "/static/others/160910_-_Betriebsreglement_ortoloco.pdf"
BYLAWS = "/static/others/160910_-_Statuten_ortoloco.pdf"
MAIL_TEMPLATE = "mails/ooooemail.html"
STYLE_SHEET = "/static/css/ortoloco.css"
BOOTSTRAP = "/static/external/oooo/bootstrap-3.3.1/css/bootstrap.min.css"
FAVICON = "/static/img/favicono.ico"
FAQ_DOC = "/static/others/FAQ_ortoloco_juli_2017.pdf"
EXTRA_SUB_INFO = "/static/others/Infoblatt_Zusatzabos.pdf"
ACTIVITY_AREA_INFO = "/static/oters/Infoblatt_Taetigkeitsbereiche.pdf"
SHARE_PRICE = "250"
PROMOTED_JOB_TYPES = ["Aktionstag"]
PROMOTED_JOBS_AMOUNT = 2
DEPOT_LIST_COVER_SHEETS = 'xxx'
DEPOT_LIST_OVERVIEWS = 'xx'
DEPOT_LIST_GENERATION_DAYS = [6]
BILLING = False
BUSINESS_YEAR_START = {"day":1, "month":1}
BUSINESS_YEAR_CANCELATION_MONTH = 9
DEMO_USER = ''
DEMO_PWD = ''
IMAGES = {'status_100': '/static/img/erbse_voll.png',
            'status_75': '/static/img/erbse_fast_voll.png',
            'status_50': '/static/img/erbse_halb.png',
            'status_25': '/static/img/erbse_fast_leer.png',
            'status_0': '/static/img/erbse_leer.png',
            'single_full': '/static/img/erbse_voll.png',
            'single_empty': '/static/img/erbse_leer.png',
            'single_core': '/static/img/erbse_voll_kernbereich.png',
            'core': '/static/img/erbse_voll_kernbereich.png'
}
GOOGLE_API_KEY = os.environ['ORTOLOCO_GOOGLE_API_KEY']


