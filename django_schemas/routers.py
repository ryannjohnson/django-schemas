"""
Cloud specific database routing based on models.

Automatic database server connections based on the type of object being
called and whether it's a read or write operation.
"""

from django.conf import settings
from .utils import dbs_by_environment, is_read_db
import random
import re

from . import ENVIRONMENTS
from .wrapper import base as WrapperBase


class ExplicitRouter:
    """Reacts solely on the model's db_name attribute."""
    
    def db_for_write(self, model, **hints):
        """Pick a write node to write on."""
        
        # Is it already defined?
        db = getattr(model._meta, 'db_name', None)
        if db:
            return db
        
        # Is there an environment we can look in?
        env = getattr(model._meta, 'db_environment', None)
        if env:
            
            # Is there a single alias for this job?
            aliases = dbs_by_environment(env, write_only=True)
            if len(aliases) == 1:
                return list(aliases)[0]
        
        # Nothing worked, return default
        return 'default'
    
    
    def db_for_read(self, model, **hints):
        """Pick a read node to read from."""
        
        # DB for write already does what we need
        alias = self.db_for_write(model, **hints)
        if alias:
            return get_random_read(alias)
        return 'default'
    
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        If database exists, use that for the basis of comparison.
        
        Allow direct relations if the databases reside in the same
        environment.
        """
        # Explicit db's?
        db1 = getattr(obj1._meta, 'db_name', None)
        db2 = getattr(obj2._meta, 'db_name', None)
        if db1 or db2:
            return db1 == db2
        
        # Same environments?
        env1 = getattr(obj1._meta, 'db_environment', None)
        env2 = getattr(obj2._meta, 'db_environment', None)
        return env1 == env2
    
    
    def allow_migrate(self, db, app_label, model=None, **hints):
        """
        Migrations will depend on the environment of the database in
        question versus the model's environment.
        """
        # Read nodes are never ok
        if is_read_db(db):
            return False
        
        # Model is required to make an assessment
        if not model:
            return None
        
        # Get each environment(s) settings
        model_env = getattr(model._meta, 'db_environment', None)
        db_envs = settings.DATABASES[db].get('ENVIRONMENTS', [])
        
        # Are neither environments set?
        if not model_env and not db_envs:
            return True
        
        # Is there a list to compare to?
        if db_envs and model_env:
            if model_env in db_envs:
                
                # Is there a specific schema to adhere to?
                global WrapperBase
                env_settings = settings.DATABASE_ENVIRONMENTS[model_env]
                specific_schema = env_settings.get('SCHEMA_NAME', None)
                
                # If there is one, adhere to it
                if specific_schema:
                    return WrapperBase.SCHEMA_NAME == specific_schema
                
                # Is an environment set on the wrapper, too?
                if WrapperBase.ENVIRONMENT_NAME:
                    return WrapperBase.ENVIRONMENT_NAME == model_env
                
                # Is it totally free range?
                if not specific_schema and not WrapperBase.SCHEMA_NAME:
                    return True
        
        # Mismatch of environment settings
        return False

        
def get_random_read(name):
    """Get's a random read replica based on the requested name.
    
    Args:
        name (str): Primary database whose name to change to a read node.
        
    Returns:
        String database name for replica, otherwise original string name.
        
    Raises:
        ValueError: If the supplied name is not a valid database option.
    
    """
    # Get all the keys that start with this name
    names = settings.DATABASES.keys()
    keys = [k for k in names if is_read_db(k, name)]
    if keys:
        
        # Pick a random read node to use
        return random.choice(keys)
        return names[index]
        
    # Does the original even exist?
    if name in names:
        return name
        
    # Return default
    return 'default'
    
    
def set_db(schema=None, db=None, environment=None):
    """Set the database wrapper variables for migration purposes.
    
    Args:
        db (Optional[str]): Name of the database to use for routing.
        schema (Optional[str]): Name of the schema to use for routing.
        environment (Optional[str]): Name of the environment for
            routing and migration.
    
    """
    global WrapperBase
    WrapperBase.SCHEMA_NAME = schema
    WrapperBase.ENVIRONMENT_NAME = environment
    WrapperBase.ALLOW_PUBLIC_SCHEMA = False
    
    # If environment is primary, then include public (for postgis)
    if environment == ENVIRONMENTS.primary:
        WrapperBase.ALLOW_PUBLIC_SCHEMA = True