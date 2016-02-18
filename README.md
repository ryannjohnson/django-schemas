# django-schemas

[![Build Status](https://travis-ci.org/ryannjohnson/django-schemas.svg?branch=master)](https://travis-ci.org/ryannjohnson/django-schemas)

Extension for Python's Django framework to support multiple schemas and migrations for PostgreSQL.

## Requirements & Installation

Currently, this package has been successfully tested with the following tools:

- PostgreSQL >= 9.3
- Python >= 3.4
- Django >= 1.9

To install via `pip`, run the following:

```sh
$ pip install django_schemas
```

## Getting Started

### Terminology

- **Environment**: refers to a group of models that are migrated as a unit. This allows for keeping different models in different schemas or databases.
- **Schema**: refers to a PostgreSQL schema, which basically equates to a namespace for tables.

### Configuration

In order to run migrations for schemas and environments, we need to add django-schemas to the list of installed apps like so:

```py
INSTALLED_APPS = (
    ...
    'django_schemas',
)
```

This package revolves around defining "environments". Environments are groups of models that can be migrated as a unit. 

To register an environment, add the following to Django's settings:

```py
DATABASE_ENVIRONMENTS = {
    'sample_environment': {},
}
```

To register a model to an environment, you must define your model as a descendant of `django_schemas.models.Model`. Also, the model must have `db_environment` defined in its meta class.

```py
from django_schemas import models

class SampleUser(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        db_environment = 'sample_environment'
```

You may continue to use `django_schemas.models` for model fields, as the module extends Django's own `models`.

Databases will need the following `ENGINE` and `ENVIRONMENTS` variables in Django's settings file, as well as adding `django_schemas.routers.ExplicitRouter` to the `DATABASE_ROUTERS` list.

```py
DATABASES = {
    'default': {
        'ENGINE': 'django_schemas.backends.postgres.wrapper',
        'NAME': 'dbname',
        'USER': 'dbuser',
        'PASSWORD': 'dbpass',
        'HOST': 'localhost',
        'PORT': '5432',
        'ENVIRONMENTS': [
            'sample_environment',
        ],
    }
}

DATABASE_ROUTERS = [
    'django_schemas.routers.ExplicitRouter',
]
```

Read replicas are automatically handled by django-schemas. To create one, append `-read#` to the alias of a new database. For example, a read replica for `default` could be `default-read1`. 

Read database selection is currently "dumb" and will use random read replicas if any are provided.

Please refer to this [sample settings file](https://github.com/ryannjohnson/django-schemas/blob/master/examples/settings.py) for more detailed explanations of how to configure your Django project settings.

### Migrating Databases

Create migrations by running Django's `makemigrations` command. 

```sh
$ ./manage.py makemigrations
```

When migrating a database schema, use the `migrate_schema` command:

```sh
$ ./manage.py migrate_schema default \
$     --environment sample_environment \
$     --schema sample_schema \
$     --big-ints
```

`default` is the alias of the database to migrate. `environment` selects the model group to migrate. `schema` names the PostgreSQL schema to migrate, and it's only required if the chosen environment doesn't have a `SCHEMA_NAME` set. `big-ints` is optional and will attempt to turn all 32-bit integer and serial columns to their respective 64-bit versions.

Migrations can also be run inside your Django project.

```py
from django_schemas.migrations import migrate
migrate(
        db='default',
        schema='sample_schema',
        environment='sample_environment',
        big_ints=True)
```

Schemas can be removed as well.

```py
from django_schemas.migrations import flush
flush(db='default', schema='sample_schema')
```

### Using Models

Django-schema models have class methods that allow you to designate databases and schemas.

```py
model_cls = SampleUser.set_db(db='default', schema='sample_schema')
```

Now whenever the model is saved or retrieved, it will use this db/schema combo:

```py
# Do insert on "default" database and "sample_schema" schema
model_cls.objects.create(name='Sample Name')

# Retrieve that same model
user1 = model_cls.objects.get(name='Sample Name')
```

Models extended from django-schemas will have a few extra methods and properties:

- `set_db(db, schema)`: Explicitly set which db and schema a model should save and query from.
- `inherit_db(cls)`: Implicitly set a model's db and schema based on another model class or model object's currently set db and schema.
- `auto_db()`: Used internally for single-schema environments.
- `db_name`: Returns the model's db.
- `schema_name`: Returns the model's schema.

*Note: This means that database models cannot have fields with the same names as these methods/properties.*

### Single-Schema Environments

Some models are designed to only exist in one place. 

To set up these models, we add an extra setting to our environment declaration:

```py
DATABASE_ENVIRONMENTS = {
    'sample_environment': {
        'SCHEMA_NAME': 'single_schema',
    },
}
```

We must also make sure that the environment is registered to **only one writable database** in Django's settings.

```py
DATABASES = {
    'default': {
        'ENGINE': 'django_schemas.backends.postgres.wrapper',
        'ENVIRONMENTS': [
            'single_schema', # 1st writable declaration here
        ],
    },
    'default-read1': {
        'ENGINE': 'django_schemas.backends.postgres.wrapper',
        'ENVIRONMENTS': [
            'single_schema', # Totally cool because this is a read replica
        ],
    },
    'other': {
        'ENGINE': 'django_schemas.backends.postgres.wrapper',
        'ENVIRONMENTS': [
            'single_schema', # 2nd writable declaration - will break the rule
        ],
    },
}
```

With this configuration, we don't have to declare any database or schema when we use models in this environment.

```py
# Both work without db/schema declarations
SampleUser.objects.create(name="Sample User 2")
SampleUser.objects.get(name="Sample User 2")
```

### Foreign Keys

Models in the same environments can be assigned relationships normally with foreign keys. When using the model API, related models will also throw an error if a model from the wrong db/schema combo try to be connected directly as an object.

```py
user1 = SampleUser.set_db('db1','schema1').objects.create(name="User 1")

# Totally works
car1 = SampleCar.inherit_db(user1).objects.create(name="Car 1", user=user1)

# Raises ValueError
car2 = SampleCar.set_db('db1','schema2').objects.create(
        name="Car 2", user=user1)
```

### PostGIS

In order to use GeoDjango's postgis backend, just switch out your databases' `ENGINE` property with `django_schemas.backends.postgis.wrapper`.

If the PostGIS extension is installed the `public` schema of your database, then you may need to add it into the `search_path` during migrations. You can do this by adding `ADDITIONAL_SCHEMAS` to your environment registration.

```py
DATABASE_ENVIRONMENTS = {
    'sample_environment': {
        'ADDITIONAL_SCHEMAS': ['public'],
    }
}
```

This will make PostGIS available when migrations try to make `geometry` columns, indexes, etc.

## Limitations

- Reverse relationships are currently unsupported via the model API.
- Model class names must not end with an underscore or contain double underscores. This is because django-schemas uses the name of the model class in order to keep track of each model created for a specific schema.