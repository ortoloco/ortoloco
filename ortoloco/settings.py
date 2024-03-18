# Django settings for ortoloco project.
import os

"""
    General Settings
"""
DEBUG = os.environ.get("JUNTAGRICO_DEBUG", "True") == "True"

ALLOWED_HOSTS = ['my.ortoloco.ch']

# test version
# ALLOWED_HOSTS = ['localhost']

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

FILE_UPLOAD_PERMISSIONS = 0o444

ROOT_URLCONF = 'ortoloco.urls'

SITE_ID = 1

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGIN_REDIRECT_URL = "/my/home"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'ortoloco.wsgi.application'

SECRET_KEY = os.environ.get('JUNTAGRICO_SECRET_KEY')

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

OAUTH2_PROVIDER = {
    'SCOPES': {
        'politoloco': 'politoloco darf einmalig deine Email sowie deinen Namen abfragen um einen Account zu erstellen',
        'beipackzettel': 'beipackzettel darf einmalig deine Email sowie deinen Namen abfragen um einen Account zu erstellen',
    },
}

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
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader'
            ],
            'debug': True
        },
    },
]


MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'impersonate.middleware.ImpersonateMiddleware',
    'django.middleware.security.SecurityMiddleware',
    #'subdomains.middleware.SubdomainURLRoutingMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
]

INSTALLED_APPS = (
    'juntagrico',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'polymorphic',
    'juntagrico_billing',
    'juntagrico_pg',
    'juntagrico_polling',
    'juntagrico_webdav',
    'crispy_forms',
    'impersonate',
    'adminsortable2',
    'oauth2_provider',
    'oidc_provider',
    'share_info',
    'ortoloco',
    'debug_toolbar',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)


"""
    Email Settings
"""
WHITELIST_EMAILS = []


def whitelist_email_from_env(var_env_name):
    email = os.environ.get(var_env_name)
    if email:
        WHITELIST_EMAILS.append(email.replace('@gmail.com', '(\+\S+)?@gmail.com'))


whitelist_email_from_env("JUNTAGRICO_EMAIL_USER")

if DEBUG is True:
    for key in list(os.environ.keys()):
        if key.startswith("JUNTAGRICO_EMAIL_WHITELISTED"):
            whitelist_email_from_env(key)

EMAIL_HOST = os.environ.get('JUNTAGRICO_EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('JUNTAGRICO_EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('JUNTAGRICO_EMAIL_PASSWORD')
EMAIL_PORT = int(os.environ.get('JUNTAGRICO_EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('JUNTAGRICO_EMAIL_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.environ.get('JUNTAGRICO_EMAIL_SSL', 'False') == 'True'


"""
    Admin Settings
"""
ADMINS = [
    ('Admin', os.environ.get('JUNTAGRICO_ADMIN_EMAIL')),
    ('Juntagrico', os.environ.get('JUNTAGRICO_DS_EMAIL'))
]
MANAGERS = ADMINS
SERVER_EMAIL = "it@ortoloco.ch"

"""
    Auth Settings
"""
AUTHENTICATION_BACKENDS = (
    'juntagrico.util.auth.AuthenticateWithEmail',
    'django.contrib.auth.backends.ModelBackend',
    'oauth2_provider.backends.OAuth2Backend',
)

"""
    DB Settings
"""
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('JUNTAGRICO_DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('JUNTAGRICO_DATABASE_NAME', 'ortoloco.db'),
        'USER': os.environ.get('JUNTAGRICO_DATABASE_USER'),
        'PASSWORD': os.environ.get('JUNTAGRICO_DATABASE_PASSWORD'),
        'HOST': os.environ.get('JUNTAGRICO_DATABASE_HOST'),
        'PORT': os.environ.get('JUNTAGRICO_DATABASE_PORT', False),
    }
}

"""
    Caching  Settings
"""
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'oooo_cache_table',
        'TIMEOUT': None,
    }
}

"""
    Localization Settings
"""
LANGUAGE_CODE = 'de-CH'
USE_I18N = True
USE_L10N = True

USE_TZ = True
TIME_ZONE = 'Europe/Zurich'

# Custom locale formats setting decimal point for de-CH
FORMAT_MODULE_PATH = [
     'ortoloco.formats',
 ]

"""
    Static Settings
"""
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_URL = '/static/'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

STATICFILES_DIRS = ( 
    os.path.join(BASE_DIR, 'static_general'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

"""
    Impersonate Settings
"""
IMPERSONATE = {
    'REDIRECT_URL': '/my/profile',
}

"""
    File & Storage Settings
"""
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

MEDIA_ROOT = 'media'


"""
     Crispy Settings
"""
CRISPY_TEMPLATE_PACK = 'bootstrap4'

"""
    Subdomain Settings
"""
# A dictionary of urlconf module paths, keyed by their subdomain.
'''SUBDOMAIN_URLCONFS = {
    None: 'ortoloco.urls', 
    'www': 'ortoloco.urls',
    'my': 'ortoloco.myurlsredirect',
    'ortoloco': 'fuckoff'
}
'''

"""
    Juntagrico Settings
"""
VOCABULARY = {
    'member': 'Loco',
    'member_pl': 'Locos',
    'assignment': 'Böhnli',
    'assignment_pl': 'Böhnlis',
    'share': 'Anteilschein',
    'share_pl': 'Anteilscheine',
    'subscription': 'Abo',
    'subscription_pl': 'Abos',
    'co_member': 'Mitabonnent',
    'co_member_pl': 'Mitabonnenten',
    'price': 'Betriebsbeitrag',
    'member_type': 'Mitglied',
    'member_type_pl': 'Mitglieder',
    'depot': 'Depot',
    'depot_pl': 'Depots'
}
ORGANISATION_NAME = "ortoloco"
ORGANISATION_LONG_NAME = "Genossenschaft ortoloco - die Hofkooperative im Fondli"
ORGANISATION_ADDRESS = {"name": "ortoloco",
                        "street": "Spreitenbacherstrasse",
                        "number": "35",
                        "zip": "8953",
                        "city": "Dietikon", }
ORGANISATION_BANK_CONNECTION = {"PC": "85-199010-5",
                                "IBAN": "CH6109000000156196402",
                                "BIC": "POFICHBEXXX",
                                "NAME": "PostFinance"}
INFO_EMAIL = "info@ortoloco.ch"
SERVER_URL = "www.ortoloco.ch"
BUSINESS_REGULATIONS = "https://www.ortoloco.ch/dokumente/ortoloco_Betriebsreglement.pdf"
BYLAWS = "https://www.ortoloco.ch/dokumente/ortoloco_Statuten.pdf"
MAIL_TEMPLATE = "mails/ooooemail.html"
EMAILS = {
    's_created': 'mails/oooo_share_created.txt',
    'j_notify': 'mails/oooo_area_jobs_contacts.txt',
}
STYLES = {'static': ['css/myortoloco.css']}
FAVICON = "/static/img/favicono.ico"
FAQ_DOC = "https://www.ortoloco.ch/dokumente/ortoloco_FAQ.pdf"
EXTRA_SUB_INFO = "https://www.ortoloco.ch/dokumente/ortoloco_Zusatzabos.pdf"
ACTIVITY_AREA_INFO = ""
SHARE_PRICE = "250"
PROMOTED_JOB_TYPES = ["Aktionstag"]
PROMOTED_JOBS_AMOUNT = 2
DEPOT_LIST_GENERATION_DAYS = [3]
DEFAULT_DEPOTLIST_GENERATORS = ['ortoloco.util.depot_list.depot_list_generation']
BILLS_USERMENU = True

BUSINESS_YEAR_START = {"day": 1, "month": 1}
BUSINESS_YEAR_CANCELATION_MONTH = 9
MEMBERSHIP_END_MONTH = 6
MEMBERSHIP_END_NOTICE_PERIOD = 9
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
DEFAULT_MAILER = 'ortoloco.mailer.Mailer'

OIDC_USERINFO = 'ortoloco.oidc_provider_settings.userinfo'
OIDC_EXTRA_SCOPE_CLAIMS = 'ortoloco.oidc_provider_settings.CustomScopeClaims'

FROM_FILTER = {'filter_expression': '.*@ortoloco\.ch',
               'replacement_from': 'info@ortoloco.ch'}

SUB_OVERVIEW_FORMAT = {
    'delimiter': ' + ',
    'format': '{amount}x {type}'
    }

def show_toolbar(request):
    return os.environ.get("DEBUG_TOOLBAR") == "True" and request.user and request.user.is_superuser

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'ortoloco.settings.show_toolbar',
}

"""
    juntagrico-billing Settings
"""
BILLS_USERMENU = True

DEFAULT_FROM_EMAIL = INFO_EMAIL

MAILER_RICHTEXT_OPTIONS = {
    'valid_styles': {
        '*': 'color,text-align,font-size,font-weight,font-style,font-family,text-decoration'
    },
    'toolbar': "undo redo | bold italic | alignleft aligncenter alignright alignjustify | outdent indent | "
               "bullist numlist | link | fontselect fontsizeselect",
}

# hack to allow multiple products(sizes) on a subscription type
ORTOLOCO_PRODUCTS = [{'name': 'Gemüse', 'sizes': [{'name': 'Tasche', 'key': 'gmues'}]},
                {'name': 'Obst', 'sizes': [{'name': 'Portion', 'key': 'obst'}]},
                {'name': 'Brot', 'sizes': [{'name': '500g', 'key': 'brot'}]},
                {'name': 'Eier', 'sizes': [{'name': 'Schachtel', 'key': 'eier'}]},
                {'name': 'Tofu', 'sizes': [{'name': 'Portion', 'key': 'tofu'}]}]

ORTOLOCO_TYPE_SUBSCRIPTIONS = {
    "gmues": [6, 7, 8, 9, 10, 11, 12, 13, 18],
    "obst": [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 31],
    "brot": [8, 9, 12, 13, 16, 17, 19, 20],
    "tofu": [30],
    "eier": [23]
}

# test version
# ORTOLOCO_TYPE_SUBSCRIPTIONS = {
#     "gmues": [1],
#     "obst": [2],
#     "brot": [3],
#     "tofu": [4],
#     "eier": [5]
# }

# hack to allow tours
ORTOLOCO_TOURS = [
    {"name": "Fondli", "depot_ids": [6, 17], "local": True},
    {"name": "kleines Auto (Renault)", "depot_ids": [20, 13, 14, 3, 7, 10, 9, 15], "local": False},
    {"name": "grosses Auto (Opel)", "depot_ids": [8, 12, 11, 2, 16, 5, 18, 19], "local": False}
]

# test version
# ORTOLOCO_TOURS = [
#     {"name": "Fondli", "depot_ids": [1, 12], "local": True},
#     {
#         "name": "kleines Auto (Renault)",
#         "depot_ids": [2, 3, 4, 5, 11, 13, 14],
#         "local": False,
#     },
#     {
#         "name": "grosses Auto (Opel)",
#         "depot_ids": [6, 7, 8, 9, 10, 15, 16, 17],
#         "local": False,
#     },
# ]

ORTOLOCO_RECURRING_MESSAGES = [
    {
        "message": "OHNE TOFU"
        ,"year": 2024
        ,"weeks": list(range(1, 50, 2))
    }
]

ORTOLOCO_AREA_NOTIFY = {
    "Verteilen": 2
}