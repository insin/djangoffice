# Django settings for officeaid project.

import os
DIRNAME = os.path.dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG
USE_I8N = False

ADMINS = (
    ('Jonathan Buchanan', 'jonathan.buchanan@gmail.com'),
)

MANAGERS = ADMINS

INTERNAL_IPS = (
    '127.0.0.1',
)

# Development database settings
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os.path.join(DIRNAME, 'database.db')

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'Europe/Belfast'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# Absolute path to the directory that holds media.
MEDIA_ROOT = os.path.join(DIRNAME, 'media')

# URL that handles the media served from MEDIA_ROOT.
# Example: 'http://media.lawrence.com/'
MEDIA_URL = 'http://localhost/media/officeaid/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '4z-(+=l(wkd)1aj+wn)(r%6z)*s*thfbi9u%1&uu_w$ids#ww='

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

CACHE_BACKEND = 'dummy:///'

ROOT_URLCONF = 'officeaid.urls'

# Authentication settings
AUTH_PROFILE_MODULE = 'officeaid.UserProfile'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/jobs/'

TEMPLATE_DIRS = (
    os.path.join(DIRNAME, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'officeaid.context_processors.app_constants',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django_docs',
    'dbsettings',
    'officeaid',
)

# Application constants
APPLICATION_NAME = 'OfficeAid&copy;'
APPLICATION_VERSION = '1.5'

# Number of items on each when paginating
ITEMS_PER_PAGE = 15

# Admininstration Job id
ADMIN_JOB_ID = 1

# Company Details
COMPANY_NAME = 'Generitech'
COMPANY_ADDRESS = {
    'street_line_1': '123 Fake St.',
    'street_line_2': 'Fiction Road',
    'town_city': 'Madeupstown',
    'postcode': 'BT12 34S6',
}
COMPANY_CONTACT = {
    'phone_number': '028 1234 5678',
    'fax_number': '028 1234 5679',
    'email': 'info@generitech.co.uk',
}
COMPANY_URL = 'http://www.generitech.co.uk'

# Load local settings if present - place setting modifications in a
# local_settings module rather than editing this file, which should
# contain development settings.
try:
    from officeaid.local_settings import *
except ImportError:
    pass
