from django.conf import settings
from django.core.management import call_command
from django_schemas.utils import get_databases, get_database


DATABASE_DEFAULT = {
    'ENGINE': 'django_schemas.backends.postgres.wrapper',
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
            'SCHEMA_NAME': 'test1_a',
            'ADDITIONAL_SCHEMAS': ['public'],
        },
        'test1-b': {
            'ADDITIONAL_SCHEMAS': ['public'],
        },
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
                    'test1-b',
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
                'ENGINE': 'django_schemas.backends.postgis.wrapper',
                'NAME': 'django_schemas_2',
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
    TEST_RUNNER='tests.runner.Runner',
    SECRET_KEY='testingtestingtesting',
    MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
    ),
    INSTALLED_APPS=(
        'django.contrib.gis',
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

call_command('test','tests')