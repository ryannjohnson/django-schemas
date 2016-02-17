from django.conf import settings
from django.db.models import *
from django.db import models as django_models
from django.utils.translation import ugettext_lazy as _

from .exceptions import ConfigError
from .utils import dbs_by_environment


# Allow custom variables into the meta class.
# http://stackoverflow.com/questions/1088431/adding-attributes-into-django-models-meta-class
CUSTOM_META_VARS = ('db_name', 'schema_name', 'table_name', 'db_environment',)
options.DEFAULT_NAMES = options.DEFAULT_NAMES + CUSTOM_META_VARS


class BaseModel:
    """
    Plain non-model class with attributes to merge into the django
    model.
    
    This model is seperate from the models.Model inheritance track so
    that it can be inherited alongside it when Django models are cloned
    for database/schema purposes.
    """
    
    @classmethod
    def set_db(cls, db=None, schema=None, **kwargs):
        """
        This method creates a new class out of the current one with
        modified meta attributes suited for multi-schema databases.
        
        Args:
            cls (Model): The current class.
            db (str): Alias to the database this model should use.
            schema (str): Name of the database schema.
        
        Returns:
            Returns a copy of this class with modified attributes.
        
        """
        from .modelsfactory import clone_model
        return clone_model(cls, db=db, schema=schema)
    
    @classmethod
    def inherit_db(cls, model):
        """
        This method is a shortcut for a model class to absorb the
        database and schema of another model (object or class).
        
        Args:
            model (mixed): Django model class or object.
        
        Returns:
            A copy of this class with modified attributes.
        
        """
        db = getattr(model._meta, 'db_name', None)
        schema = getattr(model._meta, 'schema_name', None)
        
        # Were they set alread?
        if not db or not schema:
            new_model = model.auto_db() # Throws a ConfigError
            db = new_model._meta.db_name
            schema = new_model._meta.schema_name
        
        # Return the new class
        return cls.set_db(db=db, schema=schema)
    
    @classmethod
    def auto_db(cls, **kwargs):
        """
        This method creates a new class out of the current one with
        modified meta attributes suited for multi-schema databases.
        
        Instead of manually inputing db and schema names, this method
        attempts to automatically find them.
        
        Returns:
            Returns a copy of this class with modified attributes.
        
        """
        # Based on environment, a schema might already be set
        env = getattr(cls._meta, 'db_environment', None)
        if not env:
            raise ConfigError(cls.__name__ + " has no specified environment")
        
        # Schema set by environment?
        conf = settings.DATABASE_ENVIRONMENTS[env]
        if not conf.get('SCHEMA_NAME', None):
            raise ConfigError(cls.__name__ + " has no specified schema")
        
        # Single db for this class?
        dbs = dbs_by_environment(env)
        if len(dbs) != 1:
            raise ConfigError(cls.__name__ + " has no single database")
        
        # It worked!
        return cls.set_db(db=list(dbs)[0], schema=conf['SCHEMA_NAME'])
    
    @property
    def db_name(self):
        """Respond with the database name attached to this model."""
        db = getattr(self._meta, 'db_name', None)
        if not db:
            db = getattr(self.auto_db()._meta, 'db_name', None)
        return db
    
    @property
    def schema_name(self):
        """Respond with the schema name attached to this model."""
        schema = getattr(self._meta, 'schema_name', None)
        if not schema:
            schema = getattr(self.auto_db()._meta, 'schema_name', None)
        return schema
    
    @property
    def table_name(self):
        """Respond with the table name attached to this model."""
        name = getattr(self._meta, 'table_name', None)
        if name:
            return name
        return getattr(self._meta, 'db_table', None)

class Model(BaseModel, django_models.Model):
    """Layer in front of Django models."""
    
    def __init__(self, *args, **kwargs):
        """Append some meta on instantiation."""
        
        # Do what models do first
        super(Model, self).__init__(*args, **kwargs)
        
        # Based on environment, change some of the meta information
        env = getattr(self._meta, 'db_environment', None)
        if env:
            
            # Get the environment config
            conf = settings.DATABASE_ENVIRONMENTS[env]
            if (conf.get('SCHEMA_NAME', None) and
                    not getattr(self._meta, 'schema_name', None)):
                self._meta.schema_name = conf['SCHEMA_NAME']
                self._meta.table_name = self._meta.db_table
                self._meta.db_table = '%s\".\"%s' % (
                        self._meta.schema_name, self._meta.table_name)
    
    class Meta:
        abstract = True