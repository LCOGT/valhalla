from valhalla.settings import *  # noqa
import logging
"""
Settings specific to running tests. Using sqlite will run tests 100% in memory.
https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/unit-tests/#using-another-settings-module
This file should be automatically used during tests, but you can manually specify as well:
./manage.py --settings=valhalla.test_settings
"""
logging.disable(logging.CRITICAL)
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
DEBUG = False
TEMPLATE_DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'LOCATION': 'unique-snowflake'
    },
    'locmem': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'LOCATION': 'locmem-cache'
    }
}
