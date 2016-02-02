"""
Taken from https://pytest-django.readthedocs.org/en/latest/configuring_django.html#using-django-conf-settings-configure
"""
from django.conf import settings

from django_schemas.utils import get_databases, get_database


def pytest_configure():
    from django.conf import settings
    
    DATABASE_DEFAULT = {
        'ENGINE': 'django_schemas.backends.postgis.wrapper',
        'NAME': 'django_schemas',
        'USER': 'django_schemas',
        'PASSWORD': 'django_schemas',
        'HOST': 'localhost',
        'PORT': '5432',
        'ENVIRONMENTS': [],
    }
    settings.configure(
        DATABASE_ENVIRONMENTS={
            'test1-a': {
                'SCHEMA_NAME': 'test1-a',
                'ADDITIONAL_SCHEMAS': ['public'],
            },
            'test1-b': {},
            'test2': {},
            'test3': {},
            'test4': {},
            'test5': {},
        },
        DATABASES=get_databases(
            get_database(
                alias='default',
                override={
                    'ENVIRONMENTS': ['default']
                },
                original=DATABASE_DEFAULT),
            get_database(
                alias='db1',
                override={
                    'ENVIRONMENTS': [
                        'test1-a',
                        'test2',
                        'test3',
                        'test4',
                        'test5',
                    ],
                },
                replicas=[
                    'localhost',
                ],
                original=DATABASE_DEFAULT),
            get_database(
                alias='db2',
                override={
                    'ENVIRONMENTS': [
                        'test1-b',
                    ],
                },
                original=DATABASE_DEFAULT),
        ),
        DATABASE_ROUTERS=[
            'django_schemas.routers.ExplicitRouter',
        ],
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        SECRET_KEY='testingtestingtesting',
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
        ),
        INSTALLED_APPS=(
            'django_schemas',
            'tests',
        ),
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.MD5PasswordHasher',
        ),
    )

    try:
        import django
        django.setup()
    except AttributeError:
        pass