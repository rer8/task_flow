import dj_database_url

from .base import *

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

import dj_database_url

DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL")
    )
}

#SECURE

#if not DEBUG:
#    SECURE_HSTS_SECONDS = 31536000
#    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#    SECURE_HSTS_PRELOAD = True
#    SECURE_SSL_REDIRECT = True
#    SESSION_COOKIE_SECURE = True
#    CSRF_COOKIE_SECURE = True
