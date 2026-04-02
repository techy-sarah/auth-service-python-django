# from .base import *
# from decouple import config

# DEBUG = False
# ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

from .base import *
from decouple import config

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'