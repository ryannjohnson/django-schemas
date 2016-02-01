from django_schemas.utils import get_databases, get_database


INSTALLED_APPS = (
    'django_schemas',
)
"""Register django_schemas as an app.

This is only important for using the `migrate_schema` command from the
cli. 
"""


DATABASE_ROUTERS = [
    'django_schemas.routers.ExplicitRouter',
]
"""Router that uses Models' explicit database declarations.

This router is essential for django_schemas to work correctly. Without
it, the database _meta information appended to models will be ignored.
"""


DATABASE_ENVIRONMENTS = {
    'primary': {
        'SCHEMA_NAME': 'primary_schema',
        'ADDITIONAL_SCHEMAS': ['public'],
    },
    'secondary': {},
}
"""Sets up database environments for django_schemas.

Environments become most important regarding models and their
migrations. When migrating, a database, environment, and schema are
selected. 

If the environment only has a single schema, then it can be listed as
SCHEMA_NAME. Another advantage of this is that Models specific to an
environment that is assigned to a single write-database with a single
SCHEMA_NAME will not need explicit `set_db` calls in program code.

ADDITIONAL_SCHEMAS includes other schemas in postgres's search_path
during migrations. For instance, 'public' might be required if the
PostGIS extension is installed on 'public' and is used in this other
schema.
"""


DATABASE_DEFAULT = {
    'ENGINE': 'django_schemas.backends.postgis.wrapper',
    'NAME': 'dbname',
    'USER': 'dbuser',
    'PASSWORD': 'dbpass',
    'HOST': 'localhost',
    'PORT': '5432',
    'ENVIRONMENTS': [],
}
"""Sets up the database default template.

This variable doesn't inherently do anything. Instead, we will use
these settings as shortcuts for subsequent databases. See DATABASES...
"""


DATABASES = get_databases(
    
    # Must provide a default database (Django requirement)
    get_database(
        alias='default',
        override={
            'ENVIRONMENTS': ['default']
        },
        original=DATABASE_DEFAULT),
    
    # Primary database connection (for master tables)
    get_database(
        alias='primary',
        override={
            'ENVIRONMENTS': [
                'primary',
            ],
            'HOST': 'localhost',
        },
        replicas=[
            'server1.domain.com',
            'server2.domain.com',
        ],
        original=DATABASE_DEFAULT),
    
    # Secondary database connection (holds many schemas)
    get_database(
        name='secondary1',
        override={
            'HOST': 'localhost',
            'ENVIRONMENTS': [
                'secondary',
            ],
        },
        replicas=[
            {
                'NAME': 'dbname2',
                'USER': 'dbuser2',
                'PASSWORD': 'dbpass2',
                'HOST': 'server3.domain.com',
            },
            {
                'NAME': 'dbname3',
                'USER': 'dbuser3',
                'PASSWORD': 'dbpass3',
                'HOST': 'server3.domain.com',
            },
        ],
        original=DATABASE_DEFAULT),
    
)
"""Master database list for Django.

Since scalability is the point of django_schemas, shortcut functions
are used to make it easy to add read replicas and databases in general.

Every `get_database` call returns a list of tuples containing alias
names and dictionaries associated with each alias. For example:
    [
        ('default',{'HOST':'localhost', ...},),
        ('primary',{'HOST':'localhost', ...},),
        ('primary-read1',{'HOST':'server2.domain.com', ...},),
        ...
    ]

The `replicas` argument takes a list of either strings or dicts. If a
string is supplied, then it is assumed that the string is the HOST to
replace from the writable database. If it's a dict, then items are
explicitely replaced.

The `get_databases` call converts the multiple arguments from lists of
tuples into a dict conforming to Django's specifications.
"""