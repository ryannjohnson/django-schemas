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

## Quick Start

There are 4 main steps to using this package.

### 1. Django Settings

Add the following to your `settings.py` file.

```py
# Bootstraps services
INSTALLED_APPS = (
    ...
    'django_schemas',
)

# Declares your first environment
DATABASE_ENVIRONMENTS = {
    'sample_environment': {},
}

# Update `ENGINE` and add `ENVIRONMENTS`
DATABASES = {
    'default': {
        'ENGINE': 'django_schemas.backends.postgres.wrapper',
        ...
        'ENVIRONMENTS': [
            'sample_environment',
        ],
    }
}

# Add router to top of list (or alone)
DATABASE_ROUTERS = [
    'django_schemas.routers.ExplicitRouter',
    ...
]
```

### 2. Django Models

Add the following to a `models.py` file.

```py
# Import from django_schemas
from django_schemas import models

# Use imported `models` for everything
class SampleUser(models.Model):
    name = models.CharField(max_length=100)
    
    # Use value from `DATABASE_ENVIRONMENTS`
    class Meta:
        db_environment = 'sample_environment'
```

### 3. Migrations

Add models to a database and schema via the command line.

```sh
$ python manage.py makemigrations
$ python manage.py migrate_schema default \
>     --environment sample_environment \
>     --schema sample_schema
```

### 4. Use Schemas

Models have new built-in methods for databases and schemas.

```py
# Set schema manually
user_cls = SampleUser.set_db('default','sample_schema')

# Inherit schema from another model
car_cls = SampleCar.inherit_db(user_cls)

# Execute queries with schema models
user_cls.objects.create(name="Sample Name")
user1 = user_cls.objects.get(name="Sample Name")
```

## Advanced Configuration

All customization takes place in Django `settings.py` and `models.py` files.

### Environments

This package revolves around defining "environments". Environments are groups of models that can be migrated as a unit, and they are registered in this way:

```py
DATABASE_ENVIRONMENTS = {
    'sample_environment': {
        'SCHEMA_NAME': 'sample_schema',
        'ADDITIONAL_SCHEMAS': ['public'],
    },
}
```

#### Definitions

##### `sample_environment`

This is the name of the environment, which gets referred to anytime an environment must be specified. It must always have a dict as its value.

##### `SCHEMA_NAME` (optional)

If specified, it will force what schema this environment uses. This can be useful for models that only exist in one place.

##### `ADDITIONAL_SCHEMAS` (optional)

This parameter allows you to append schemas to the [search_path](http://www.postgresql.org/docs/9.3/static/sql-set.html#AEN81536) when migrating a database. A common use case is being able to use the postgis extension from the `public` schema on your custom schema.

### Databases

Databases are setup a little bit differently with django-schemas.

```py
DATABASES = {
    'default': {
        'ENGINE': 'django_schemas.backends.postgres.wrapper',
        'NAME': 'dbname',
        'USER': 'dbuser',
        'PASSWORD': 'dbpass',
        'HOST': '192.168.1.10',
        'PORT': '5432',
        'ENVIRONMENTS': [
            'sample_environment',
        ],
    },
    'default-read1': {
        'ENGINE': 'django_schemas.backends.postgres.wrapper',
        'NAME': 'dbname',
        'USER': 'dbuser',
        'PASSWORD': 'dbpass',
        'HOST': '192.168.1.11',
        'PORT': '5432',
    },
}
```

#### Definitions

##### `ENGINE`

Normally, this can only be `django_schemas.backends.postgres.wrapper`. However, if you're using PostGIS, you should use `django_schemas.backends.postgis.wrapper` instead.

##### `ENVIRONMENTS`

This is a list of environments that can be used with this database. This helps govern what migrations and operations can happen where.

In addition, if an environment's `SCHEMA_NAME` is set and only one database has that particular environment, then models assigned to that environment can now omit the `set_db()` method entirely when running queries.

##### `default-read1` (optional)

Database aliases that match the regex pattern `\-read[1-9]+\d*$` will be classified as a "read replica" by the router, and will be treated as such. 

Replicas don't need an `ENVIRONMENTS` parameter since the write database will already have it. If `ENVIRONMENTS` is set, then it will be ignored.

When read replicas are set, queries will randomly choose a replica to select from. 

### Models

Django-schemas models are extensions of Django models, so models only need to inherit from `django_schemas.models.Model` and declare a `db_environment` in their meta classes.

```py
from django_schemas import models

class SampleCar(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(SampleUser)
    
    def object_method(self):
        pass
    
    class Meta:
        db_environment = 'sample_environment'
```

## Migrations (CLI)

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

#### Definitions

##### `default` 

This is the alias of the database to migrate.

##### `--environment`

Designating an environment tells Django which models are being migrated.

##### `--schema`

This is only required for environments without a `SCHEMA_NAME`.

##### `--big-ints` (optional)
Will attempt to turn all 32-bit integer and serial columns to their respective 64-bit versions.

## Migrations (Python)

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

## Using Models

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

Within environments with a `SCHEMA_NAME` and only one database (not including read replicas), no methods are needed to set the db/schema.

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

This will make PostGIS available when migrations try to make `geometry` columns, indexes, etc.

## Limitations

- [Reverse relationships](https://docs.djangoproject.com/es/1.9/topics/db/queries/#following-relationships-backward) are currently unsupported via the model API.
- Model class names must not end with an underscore or contain double underscores. This is because django-schemas uses the name of the model class in order to keep track of each model created for a specific schema.