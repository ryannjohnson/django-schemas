from django import db as django_db
from django.conf import settings
from django.core.management import call_command
from django.db import connections, transaction

from . import routers
from .utils import dict_fetchall


def migrate(db, schema=None, environment=None, big_ints=True):
    """
    Migrate a particular database. If a schema is provided, it will
    become the default schema for the models.
    
    Args:
        db (str): Alias for the database to migrate.
        schema (Optional[str]): Name of the schema to use for
            environments that don't explicitly specify one.
        environment (Optional[str]): Name of environment, if only one
            should be migrated this round.
        big_ints (Optional[bool]): If true, any integer or serial
            fields will be converted to bigint and bigserial fields.
    
    """
    # Do this for every environment available on this db
    environments = []
    if environment:
        environments.append(environment)
    else:
        environments = settings.DATABASES[db].get('ENVIRONMENTS',[])
    for env in environments:
        
        # Figure out the schema name
        current_schema = settings.DATABASE_ENVIRONMENTS[env].get('SCHEMA_NAME')
        if not current_schema:
            current_schema = schema
        if not current_schema:
            raise Exception("schema required and not present")
        
        # Prep the database wrapper with the school we want
        routers.set_db(schema=current_schema, environment=env)
        
        # Run the migration script for this school specifically
        call_command('migrate', database=db)
        
        # Apply hack to upgrade any 'serial' and 'int' columns to their
        # 'big' counterparts.
        if big_ints:
            upgrade_to_big_keys(db=db, schema=current_schema)
        
        # Reset the router db and schema
        routers.set_db()


def flush(db, schema):
    """Drop the schema from the database.
    
    Args:
        db (str): Name of the database to write to.
        schema (str): Name of the schema to be erased.
    
    """
    cursor = connections[db].cursor()
    cursor.execute("DROP SCHEMA %s CASCADE" % schema)
    
    
def upgrade_to_big_keys(db, schema):
    """
    Database hack to detect and upgrade all keys to their
    'big' counterparts.
    
    Args:
        db (str): Database to detect from and apply upgrades to.
        schema (str): Schema to detect from and apply upgrades to.
    
    Note:
        This currently upgrades ALL 'int' and 'serial' columns to
        'bigint' and 'bigserial', regardless of their role within
        models.
    
    """
    # Start by getting all the tables in the database + schema
    cursor = connections[db].cursor()
    cursor.execute("""SELECT table_name FROM information_schema.tables
                   WHERE table_schema = %s""", (schema,))
    tables = dict_fetchall(cursor)
    
    # Scan each table for its columns
    for table in tables:
        cursor.execute("""
            SELECT
                column_name,
                data_type
            FROM
                information_schema.columns
            WHERE
                table_schema = %s
                AND table_name = %s
        """, (schema, table['table_name']))
        columns = dict_fetchall(cursor)
        
        # For each column that matches the normal data type,
        # alter it to be the bigger version of itself.
        for column in columns:
            if column['data_type'] in ['int','integer']:
                new_type = 'bigint'
            elif column['data_type'] in ['serial']:
                new_type = 'bigserial'
            else:
                continue
            full_table = "%s.%s" % (schema, table['table_name'])
            sql = "ALTER TABLE %s ALTER COLUMN %s SET DATA TYPE %s"
            cursor.execute(sql % (full_table, column['column_name'], new_type))
            
    # Commit all the queries
    # transaction.commit_unless_managed(using=db)