# core/settings/dev.py
from .base import *


DEBUG = os.getenv('DEBUG')
SECRET_KEY =  os.getenv('SECRET_KEY')
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DATABASE_URL = f'postgres://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}'


DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )
}

