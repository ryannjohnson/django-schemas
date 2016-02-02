"""
Taken from https://github.com/tomchristie/django-rest-framework/blob/master/tests/conftest.py
"""

def pytest_configure():
    from django.conf import settings
    
    DATABASE_DEFAULT = {
        'ENGINE': 'django_schemas.backends.postgis.wrapper',
        'NAME': 'dbname',
        'USER': 'dbuser',
        'PASSWORD': 'dbpass',
        'HOST': 'localhost',
        'PORT': '5432',
        'ENVIRONMENTS': [],
    }
    DATABASES = get_databases(
        get_database(
            alias='default',
            override={
                'ENVIRONMENTS': ['default']
            },
            original=DATABASE_DEFAULT),
        get_database(
            alias='primary',
            override={
                'ENVIRONMENTS': [
                    'primary',
                    'secondary',
                ],
                'HOST': 'localhost',
            },
            replicas=[
                'localhost',
            ],
            original=DATABASE_DEFAULT),
    )
    
    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES=DATABASES,
        DATABASE_ROUTERS=[
            'django_schemas.routers.ExplicitRouter',
        ],
        DATABASE_ENVIRONMENTS={
            'primary': {
                'SCHEMA_NAME': 'primary_schema',
                'ADDITIONAL_SCHEMAS': ['public'],
            },
            'secondary': {},
        },
        SITE_ID=1,
        SECRET_KEY='testingtestingtesting',
        ROOT_URLCONF='tests.urls',
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