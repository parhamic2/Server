"""
Django settings for quiz_project project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "1ef#**@xtpaj_)xipjqv_&*(=v*0=+d73bmyma4z#tq#l%nxv3"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

AUTH_USER_MODEL = "quiz.User"

# Application definition
INSTALLED_APPS = [
    "quiz",
    'rangefilter',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "rest_framework",
    "rest_framework.authtoken",
    "constance",
    "constance.backends.database",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # 'django.middleware.csrf.CsrfViewMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "quiz_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "quiz_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
        "NAME": "unity_quiz",
        "USER": "root",
        "PASSWORD": "zozpzi1o1p1i",
        "HOST": "localhost",  # Or an IP Address that your DB is hosted on
        "PORT": "3306",
        "OPTIONS": {"charset": "utf8mb4"},
    }
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Tehran"

USE_I18N = True

USE_L10N = True

USE_TZ = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static_media/")

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.RemoteUserAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

ALPHABET = ["A","B","C","Ç","D","E","F","G","Ğ","H","I","İ","J","K","L","M","N","O","Ö","P","R","S","Ş","T","U","Ü","V","Y","Z"]


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": True}
    },
}

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_CONFIG = {
    "HELP_1_LETTER_PRICE": (40, "One letter help price", int),
    "ESTIMATED_TIME": (0, "Estimated wait time", int),
    "HELP_2_LETTER_PRICE": (60, "Two letter help price", int),
    "HIDDEN_WORDS_REWARD": (20, "Reward for each hidden word", int),
    "EMAIL_VERIFY_REWARD": (300, "Reward for each hidden word", int),
    "INVITE_CODE_PARENT_REWARD": (1000, "", int),
    "INVITE_CODE_CHILD_REWARD": (800, "", int),
    "HIDDEN_WORDS_REWARD": (50, "Reward for each 10 hidden words", int),
    "AD_COINS": (50, "Reward coins for watching ad", int),
    "TIMER_RESET_PRICE": (100, "Timer reset help price", int),
    "LEVELS_XPS": ("50, 100, 200, 400, 800, 1600, 3200", "Timer reset help price", str),
    "DAILY_REWARDS": ("100, 200, 500, 1000", "Daily rewards", str),
    "MATCH_EXPIRE_TIME": (24, "Match expire time in hours.", int),
    "FRIEND_SHARE_PERCENTAGE": (10, "Poorsant", int),
    "VERSION": ("1.0.0", "Version of the game", str),
    "MOTD_TITLE": ("", "Message Of The Day", str),
    "MOTD": ("", "Message Of The Day", str),
    "MOTD_PERCENT": ("", "Message Of The Day", str),
    "UPDATE_REWARD_COINS": (200, "Reward for updating game", int),
    "UPDATE_REWARD_COPOUNS": (0, "Reward for updating game", int),
    "UPDATE_REWARD_BOOST": (0, "Reward for updating game", int),
    "UPDATE_REWARD_BOOST_TIME": (24, "Reward for updating game in Hours", int),
    "VIDEO_LINK_1": ('', "Video 1 Link", str),
    "VIDEO_LINK_2": ('', "Video 2 Link", str),
    "VIDEO_LINK_3": ('', "Video 3 Link", str),
    "VIDEO_LINK_4": ('', "Video 4 Link", str),
    "VIDEO_LINK_5": ('', "Video 5 Link", str),
    "VIDEO_LINK_6": ('', "Video 6 Link", str),
    "VIDEO_LINK_7": ('', "Video 7 Link", str),
    "VIDEO_LINK_8": ('', "Video 8 Link", str),
    "VIDEO_LINK_9": ('', "Video 9 Link", str),
    "VIDEO_LINK_10": ('', "Video 10 Link", str),
}

CELERY_BROKER_URL = "amqp://localhost"


# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#         },
#         'logfile': {
#             'level':'DEBUG',
#             'class':'logging.FileHandler',
#             'filename': BASE_DIR + "/../logfile",
#         },
#     },
#     'root': {
#         'level': 'INFO',
#         'handlers': ['console', 'logfile']
#     },
# }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.cancepper.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'canceppe'
EMAIL_HOST_PASSWORD = '768Lybp0Ul'

LANGUAGE = 'TR'