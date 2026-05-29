from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['task-flow-lqg6.onrender.com', 'localhost', '127.0.0.1']


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

import dj_database_url

DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL")
    )
}

#SECURE
#SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

#if not DEBUG:
#    SECURE_HSTS_SECONDS = 31536000
#    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#    SECURE_HSTS_PRELOAD = True
