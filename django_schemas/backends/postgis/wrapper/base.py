from django.contrib.gis.db.backends.postgis.base import DatabaseWrapper

from ... import conf


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
        if conf.SCHEMA_NAME:
            query = "CREATE SCHEMA IF NOT EXISTS %s; " % conf.SCHEMA_NAME
            search_path = conf.SCHEMA_NAME
            if conf.ADDITIONAL_SCHEMAS:
                search_path += ', ' + ', '.join(conf.ADDITIONAL_SCHEMAS)
            query += "SET search_path = %s;" % search_path
            cursor.execute(query)
        return cursor