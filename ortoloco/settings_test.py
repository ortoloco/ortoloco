"""
Settings for the tests: python manage.py test --settings=ortoloco.settings_test
"""
import os

from jwcrypto import jwk

from ortoloco.settings import *  # noqa: F401,F403
from ortoloco.settings import OAUTH2_PROVIDER

DEBUG = False
SECRET_KEY = 'test-only-secret-key'

# OpenID Connect with a throwaway key
OAUTH2_PROVIDER = {
    **OAUTH2_PROVIDER,
    'OIDC_ENABLED': True,
    'OIDC_RSA_PRIVATE_KEY': jwk.JWK.generate(kty='RSA', size=2048).export_to_pem(True, None).decode(),
}

# no collectstatic needed
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

# never send real emails, never call external services
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
EMAIL_HOST = None
VELO_CODE = None
WP_USER = WP_PASSWORD = None

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

# sqlite in memory by default, fast and without setup.
# ORTOLOCO_TEST_DATABASE=env uses the JUNTAGRICO_DATABASE_* database instead (PostgreSQL like production, used in CI)
if os.environ.get('ORTOLOCO_TEST_DATABASE') != 'env':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
