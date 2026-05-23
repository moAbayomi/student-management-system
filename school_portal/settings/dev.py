# core/settings/dev.py
from .base import *


DEBUG = os.getenv('DEBUG')
SECRET_KEY =  os.getenv('SECRET_KEY')
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"



DATABASES = {
    'default': dj_database_url.config(
         default=os.environ.get('DATABASE_URL', 'postgres://user:pass@localhost:5432/dbname'),
        conn_max_age=600,
        ssl_require=False
    )
}

