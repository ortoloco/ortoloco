# Django settings for ortoloco project.
import os
from juntagrico import defaults

"""
    General Settings
"""
DEBUG = os.environ.get("JUNTAGRICO_DEBUG", "True") == "True"

ALLOWED_HOSTS = ['my.ortoloco.ch', '127.0.0.1']

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

FILE_UPLOAD_PERMISSIONS = 0o444

ROOT_URLCONF = 'ortoloco.urls'

SITE_ID = 1

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGIN_REDIRECT_URL = "/"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'ortoloco.wsgi.application'

SECRET_KEY = os.environ.get('JUNTAGRICO_SECRET_KEY')

OAUTH2_PROVIDER = {
     'SCOPES': {
         'nextcloud': 'nextcloud darf einmalig deine Email sowie deinen Namen abfragen um einen Account zu erstellen',
     },
    'PKCE_REQUIRED': False
 }

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
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
                'juntagrico.context_processors.vocabulary',
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
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ortoloco',
    'juntagrico.apps.JuntagricoAdminConfig',
    'juntagrico_contribution',
    'juntagrico_billing',
    'juntagrico_pg',
    'juntagrico_webdav',
    'juntagrico',
    'import_export',
    'impersonate',
    'crispy_forms',
    'crispy_bootstrap4',
    'adminsortable2',
    'django_select2',
    'djrichtextfield',
    'polymorphic',
    'debug_toolbar',
    'oauth2_provider',
    'oidc_provider',
)


"""
    Email Settings
"""
EMAIL_BACKEND='ortoloco.mailer.IndividualToEmailBackend'
BATCH_MAILER = {
    'batch_size': 500,
    'wait_time': 0
}
FROM_FILTER = {'filter_expression': '.*@ortoloco\.ch',
               'replacement_from': 'info@ortoloco.ch'}
ENFORCE_MAIL_CONFIRMATION = True

EMAIL_HOST = os.environ.get('JUNTAGRICO_EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('JUNTAGRICO_EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('JUNTAGRICO_EMAIL_PASSWORD')
EMAIL_PORT = int(os.environ.get('JUNTAGRICO_EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('JUNTAGRICO_EMAIL_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.environ.get('JUNTAGRICO_EMAIL_SSL', 'False') == 'True'

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

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

STATICFILES_DIRS = [
     os.path.join(BASE_DIR, 'static_general'),
]

"""
    Impersonate Settings
"""
IMPERSONATE = {
    'REDIRECT_URL': '/my/profile',
    'URI_EXCLUSIONS': [], # enable /admin impersonation
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
    'depot_pl': 'Depots',
    'package': 'Tasche',
    'from': '{} von {}',
}

ORGANISATION_NAME = "ortoloco"
ORGANISATION_LONG_NAME = "Genossenschaft ortoloco - die Hofkooperative im Fondli"
ORGANISATION_ADDRESS = {"name": "Genossenschaft ortoloco",
                        "street": "Spreitenbacherstrasse",
                        "number": "35",
                        "zip": "8953",
                        "city": "Dietikon",
                        "extra": "Biohof Fondli"}
ORGANISATION_BANK_CONNECTION = {"PC": "85-199010-5",
                                "IBAN": "CH6109000000156196402",
                                "BIC": "POFICHBEXXX",
                                "NAME": "PostFinance"}
CONTACTS = {
    'general': "info@ortoloco.ch",
    'for_members': "info@ortoloco.ch",
    'for_subscriptions': "info@ortoloco.ch",
    'for_shares': "info@ortoloco.ch",
    'technical': "it@ortoloco.ch",
}
ORGANISATION_WEBSITE = {
    'name': "www.ortoloco.ch",
    'url': "https://www.ortoloco.ch/"
}
BUSINESS_REGULATIONS = "https://static.ortoloco.ch/documents/ortoloco_Betriebsreglement.pdf"
BYLAWS = "https://static.ortoloco.ch/documents/ortoloco_Statuten.pdf"
FAQ_DOC = "https://ortoloco.ch/faq"
GDPR_INFO = "https://www.ortoloco.ch/datenschutz"
MAIL_TEMPLATE = "mails/ooooemail.html"
EMAILS = {
    's_created': 'mails/oooo_share_created.txt',
    'j_notify': 'mails/oooo_area_jobs_contacts.txt',
}
STYLES = {'static': ['css/myortoloco.css']}
FAVICON = "/static/img/favicono.ico"
EXTRA_SUB_INFO = "https://ortoloco.ch/dokumente/zusatzabos"
ACTIVITY_AREA_INFO = ""
ENABLE_SHARES = True
REQUIRED_SHARES = 0
SHARE_PRICE = "250"

# Enable external signup API for signup through ortoloco.ch
ENABLE_EXTERNAL_SIGNUP = True

# Frontpage upcoming jobs overview configuration
JOBS_FRONTPAGE = {
    'days': 14,
    'min': 3,
    'max': 10,
    'promoted_types': ["Aktionstag"],
    'promoted_count': 2
}
ALLOW_JOB_UNSUBSCRIBE = False

'''
Depot list generation costumization
'''
def extra_context(context):
    from django.conf import settings
    from juntagrico.util.temporal import weekdays
    from django.utils import timezone
    from juntagrico.dao.depotdao import DepotDao
    from juntagrico.entity.listmessage import ListMessage

    # update recurring messages, set active flag before depot list generation
    list_week_date = timezone.localdate() + timezone.timedelta(days=7-timezone.localdate().weekday())
    recurring_message_config = settings.ORTOLOCO_RECURRING_MESSAGES
    actual_config_messages = [
        message_config
        for message_config in recurring_message_config
        if not message_config.get('year') or message_config['year'] == list_week_date.year
    ]
    delivery_calender_week = list_week_date.isocalendar().week
    for message_config in actual_config_messages:
        is_active = delivery_calender_week in message_config['weeks']
        for message in ListMessage.objects.filter(message=message_config['message']):
            if message.active != is_active:
                message.active = is_active
                message.save()

    days = DepotDao.all_depots_for_list().prefetch_related('subscription_set'). \
        values('weekday').order_by('weekday').distinct()
    for day in days:
        day['name'] = weekdays[day['weekday']]
        day['date'] = list_week_date + timezone.timedelta(days=day['weekday']-1)
    return dict(days=days)

DEPOT_LIST_GENERATION_DAYS = [3]
# the names of the lists define the url and need to stay constant for the printing script on the Gartenlaptop to work
DEPOT_LISTS = {
    'depotlist': 'exports_oooo/depotlist.html',
    'depotoverview': {
        'name': 'Depot-Übersicht',
        'template': 'exports_oooo/depot_overview.html',
        'extra_context': extra_context,
    },
    'amountoverview': {
        'name': 'Mengen-Übersicht',
        'template': 'exports_oooo/amount_overview.html',
        'extra_context': extra_context,
    },
    'touroverview': {
        'name': 'Tour-Übersicht',
        'template': 'exports_oooo/tour_overview.html',
        'extra_context': extra_context,
    },
    'tourlist': {
        'name': 'Tour-Liste',
        'template': 'exports_oooo/tour_list.html',
        'extra_context': extra_context,
    },
}

BUSINESS_YEAR_START = {"day": 1, "month": 1}
BUSINESS_YEAR_CANCELATION_MONTH = 9
MEMBERSHIP_END_MONTH = 6
MEMBERSHIP_END_NOTICE_PERIOD = 9
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

OIDC_USERINFO = 'ortoloco.oidc_provider_settings.userinfo'
OIDC_EXTRA_SCOPE_CLAIMS = 'ortoloco.oidc_provider_settings.CustomScopeClaims'


SUB_OVERVIEW_FORMAT = {
   'delimiter': ' + ',
   'format': '{amount}x{type}'
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
BEXIO_EXPORT = True

"""
    juntagrico rich text editor options
"""
DJRICHTEXTFIELD_CONFIG = defaults.richtextfield_config(
    LANGUAGE_CODE,
    mailer = {
            'valid_styles': {
                '*': ''
            },
            'toolbar': "undo redo | bold italic | h1 h2 h3 | alignleft aligncenter | outdent indent | "
                       "bullist numlist | link",
    }
)

# depot list recurring messages
ORTOLOCO_RECURRING_MESSAGES = [
    {"message": "OHNE TOFU", "year": 2025, "weeks": list(range(1, 50, 2))},
    {"message": "OHNE TOFU", "year": 2026, "weeks": set(range(1, 50, 2))},
    {"message": "MIT TOFU", "year": 2026, "weeks": set(range(1,53)) - set(range(1, 50, 2))},
    {"message": "OHNE TOFU", "year": 2027, "weeks": set(range(2, 51, 2))},
    {"message": "MIT TOFU", "year": 2027, "weeks": set(range(1,53)) - set(range(2, 51, 2))},
]

# days in advance for area admin notification about job participants
ORTOLOCO_AREA_NOTIFY = {
    "Verteilen": 2
}

# juntagrico export permission level
IMPORT_EXPORT_EXPORT_PERMISSION_CODE = 'view'

# wordpress content integration into my.ortoloco
WP_USER = os.environ.get('WP_USER')
WP_PASSWORD = os.environ.get('WP_PASSWORD')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '[%(asctime)s] %(levelname)s %(message)s'}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

# Staging
if os.environ.get('JUNTAGRICO_STAGING') == '1':
    ALLOWED_HOSTS.append('ortoloco-staging.juntagrico.science')
    EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
    STYLES['static'].append('css/staging.css')
