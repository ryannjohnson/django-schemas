# django-schemas

[![Build Status](https://travis-ci.org/ryannjohnson/django-schemas.svg?branch=master)](https://travis-ci.org/ryannjohnson/django-schemas)

Extension for Python's Django framework to support multiple schemas and migrations for PostgreSQL.

## Requirements

- PostgreSQL >= 9.3
- Python >= 3.4
- Django >= 1.9

## Getting Started

### Installation

#### Pip

This package isn't registered on pypi yet, but you can install it straight from the repo like this:

```sh
$ pip install git+ssh://git@github.com/ryannjohnson/django-schemas.git
```

### Terminology

In the context of django-schemas, there are a few terms that need explaining:

- **Environment**: Refers to a group of models that are migrated as a unit. This allows for keeping different models in different schemas or databases.

### Configuration

In order to run migrations for schemas and environments, we need to add django-schemas to the list of installed apps like so:

```py
INSTALLED_APPS = (
    'django_schemas',
)
```

This package revolves around defining "environments" for models to be a part of. Every model can be a member of a single environment, and every database can contain any number of environments.

To register an environment, add the following to Django's settings:

```py
DATABASE_ENVIRONMENTS = {
    'sample_environment': {},
}
```

And to register a model to that environemnt, have the model and its fields use django-schemas' `models` module and add the `db_environment` to the model's `Meta` class.

```py
from django_schemas import models

class SampleUser(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        db_environemnt = 'sample_environment'
```

Lastly for configuration, databases that use django-schemas will need to use the django-schemas `ENGINE` and include an `ENVIRONMENTS` variable to implement database routing.

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

For read replica databases, just add another database and append `-read#` to the alias. For example, a read replica for `default` could be `default-read1`. If any read replicas are set in this way, django-schemas' `ExplicitRouter` will automatically use them for applicable model read operations.

Keep in mind that instantiated django-schemas models are each bound to a specific **database** and **schema**, so read replica rules will only apply for models attached to a database with a read replica present. 

Please refer to this [sample settings file](https://github.com/ryannjohnson/django-schemas/blob/master/examples/settings.py) for more detailed explainations of how to configure your Django project.

### Migrating Databases

Making migrations on Django is no different than usual. 

```sh
$ ./manage.py makemigrations
```

When migrating a database, the `migrate_schema` command is used:

```sh
$ ./manage.py migrate_schema default \
$     --environment sample_environment \
$     --schema sample_schema \
$     --big-ints
```

The `default` argument is referring to the database alias you'd like to migrate. The `environment` option refers to the model group you're migrating. The `schema` option is any schema of your choosing. The `big-ints` option is optional and will attempt to turn all 32-bit integers and serials to 64-bit versions of themselves.

Migrations can also be run from within Django.

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

- **`set_db(db, schema)`**: Explicitly set which db and schema a model should save and query from.
- **`inherit_db(cls)`**: Implicitly set a model's db and schema based on another model class or model object's currently set db and schema.
- **`auto_db()`**: See below.
- **`db_name`**: Returns the model's db.
- **`schema_name`**: Returns the model's schema.

*Note: This does mean that database models cannot have fields with the same names as these methods/properties.*

### Single-Schema Environments

Sometimes, there's no reason to use multiple schemas or databases for models. Some models just exist in one place.

To set up these models, we add an extra setting to our environment declaration:

```py
DATABASE_ENVIRONMENTS = {
    'sample_environment': {
        'SCHEMA_NAME': 'single_schema',
    }
}
```

Also, we must make sure that the environment is registered to **only one writable database** in Django's settings.

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
    }
}
```

With this configuration, we don't have to declare any database or schema when we use models in this environment.

```py
# Both work without db/schema declarations
SampleUser.objects.create(name="Sample User 2")
SampleUser.objects.get(name="Sample User 2")
```

### Foreign Keys

Models in the same environments can be assigned relationships normally with foreign keys. When using the model api, related models will also throw an error if a model from the wrong db/schema combo try to be connected directly as an object.

```py
user1 = SampleUser.set_db('db1','schema1').objects.create(name="User 1")

# Totally works
car1 = SampleCar.inherit_db(user1).objects.create(name="Car 1", user=user1)

# Raises ValueError
car2 = SampleCar.set_db('db1','schema2').objects.create(
        name="Car 2", user=user1)
```

## Limitations

- Reverse relationships are currently unsupported via the model API.
- Model class names must not end with an underscore or contain double underscores. This is because django-schemas uses the name of the model class in order to keep track of each model created for a specific schema.