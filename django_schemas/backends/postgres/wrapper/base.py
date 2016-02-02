from django.db.backends.postgresql_psycopg2.base import DatabaseWrapper

from ...conf import ADDITIONAL_SCHEMAS, SCHEMA_NAME


class DatabaseWrapper(DatabaseWrapper):
    """
    This wrapper will set the search path depending on whether 
    a or not a SCHEMA_NAME is supplied. 
    
    Source:
        http://stackoverflow.com/questions/1160598/how-to-use-schemas-in-django#answer-18391525
    
    """
    
    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

    def _cursor(self):
        """Database cursor to write whatever we want. 
        
        Typically used for migrations, this function will check
        to see if SCHEMA_NAME is set or not. If it is, then it 
        will create it if it doesn't yet exist. Finally, it will
        point to that schema.
        """
        cursor = super(DatabaseWrapper, self)._cursor()
        if SCHEMA_NAME:
            query = "CREATE SCHEMA IF NOT EXISTS %s; " % SCHEMA_NAME
            search_path = SCHEMA_NAME
            if ADDITIONAL_SCHEMAS:
                search_path += ', ' + ', '.join(ADDITIONAL_SCHEMAS)
            query += "SET search_path = %s;" % search_path
            cursor.execute(query)
        return cursor