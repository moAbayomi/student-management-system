# core/settings/dev.py
from .base import *
import dj_database_url



# os.getenv returns a string, and the string 'False' is truthy, so compare explicitly
DEBUG = os.getenv('DEBUG', 'True').lower() in ('1', 'true', 'yes')
SECRET_KEY =  os.getenv('SECRET_KEY')
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025  # Default SMTP port for Mailpit
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False



DATABASES = {
    'default': dj_database_url.config(
         default=os.environ.get('DATABASE_URL', 'postgres://user:pass@localhost:5432/dbname'),
        conn_max_age=600,
        ssl_require=False
    )
}

