from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    CORS_ALLOWED_ORIGINS=(list, ['http://localhost:5173']),
)
# Local development reads .env; in Docker/CI the variables come from the environment.
if (BASE_DIR / '.env').exists():
    environ.Env.read_env(str(BASE_DIR / '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third party
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'corsheaders',
    # project
    'food',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'resturant.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'food.context_processors.categories',
            ],
        },
    },
]

WSGI_APPLICATION = 'resturant.wsgi.application'


# Database: PostgreSQL when DB_NAME is set (Docker/production), SQLite otherwise.
if env('DB_NAME', default=''):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME'),
            'USER': env('DB_USER'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST', default='localhost'),
            'PORT': env('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True


# Static & media files

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

# Used by the browsable API login page.
LOGIN_URL = 'rest_framework:login'
LOGIN_REDIRECT_URL = '/api/'
LOGOUT_REDIRECT_URL = '/api/'


# Django REST framework

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # browsable API
    ),
    # Secure by default: public endpoints opt in with AllowAny / IsAdminOrReadOnly.
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '300/min',
        'anon': '100/min',
        'login': '20/min',
        'register': '20/min',
        'comment': '30/min',
        'order': '120/min',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Restaurant API',
    'DESCRIPTION': (
        'REST API for a restaurant: menu, cart, checkout, orders, comments and favorites.\n\n'
        '## Try it in 4 steps\n'
        '1. **Auth → Register** to create an account.\n'
        '2. **Auth → Log in** and copy the `access` token from the response.\n'
        '3. Click **Authorize** (top right) and paste the token. Swagger adds `Bearer` for you.\n'
        '4. Follow the flow: **Menu → List foods**, **Cart → Add a food to the cart**, '
        '**Cart → Checkout**, **Orders → List my orders**.\n\n'
        'List endpoints are paginated (10 per page, use `?page=2`). '
        'A Postman collection with the same flow is in the repository (`docs/`).'
    ),
    'VERSION': '1.0.0',
    'CONTACT': {'name': 'Source code on GitHub', 'url': 'https://github.com/alyhoseinpoor/restaurant'},
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVERS': [{'url': 'http://localhost:8000', 'description': 'Local development'}],
    # Order of the groups in Swagger UI follows the user flow.
    'TAGS': [
        {'name': 'Auth', 'description': 'Register and get JWT tokens.'},
        {'name': 'Menu', 'description': 'Categories and foods. Public to read, staff only to change.'},
        {'name': 'Cart', 'description': 'The logged-in user\'s cart and checkout.'},
        {'name': 'Orders', 'description': 'Order history and cancellation.'},
        {'name': 'Comments', 'description': 'Food comments. New comments wait for admin approval.'},
        {'name': 'Favorites', 'description': 'Foods saved by the logged-in user.'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,  # keep the token after a page reload
        'displayRequestDuration': True,
        'docExpansion': 'none',  # start collapsed; open one group at a time
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')
