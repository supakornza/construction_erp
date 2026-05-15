from .base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'construction_erp',
        'USER': 'postgres',
        'PASSWORD': 'postgres1234',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

INTERNAL_IPS = ['127.0.0.1']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
