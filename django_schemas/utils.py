from copy import deepcopy
from django.conf import settings
import inspect
import logging
import re


def get_databases(*groups):
    """Wrapper used to return database (str, list) tuples into a dict.
    
    Args:
        default (dict): The default database configuration to modify.
        groups (*args): List of lists of tuples to convert into a dict
            Eg. [[(name1, value1), (name2, value2)], [(name3, value3)]}
        
    Returns:
        Dictionary of key-value pairs.
    
    """
    output = {}
    for pairs in groups:
        for name, info in pairs:
            output[name] = info
    return output
    

def get_database(alias, override=None, replace=None, replicas=None, original=None):
    """Return the _GET_DATABASES_DEFAULT variable with any changes specified.
    
    Args:
        alias (str): The alias of the database (used by Django).
        override (dict): Any keys and values to override the defaults with.
        replicas (list): Host names to be used as read-replicas.
        replace (bool): If override is set, then just output override.
        original (dict): Optional original model to start from.
    
    Returns:
        List of tuples of str, dict pairs.
    
    Raises:
        TypeError: If `replicas` is not an instance of `list`.
    
    """
    # Start with the default
    original = deepcopy(original)
    appending = original
    output = []
    if override:
        
        # Do we get rid of all the original settings?
        if replace:
            appending = deepcopy(override)
            
        # Only replace key by key
        else:
            for key in override:
                original[key] = override[key]
    
    # Append this first one to the list.
    # `appending` will still reflect the `original` list due to referencing
    output.append((alias, appending))
    
    # Are replicas included?
    if replicas:
        if isinstance(replicas, list):
            formatted = get_database_replicas_list(alias, original, replicas)
            output.extend(formatted)
        else:
            raise TypeError("replicas must be a list")
    
    # Return tuple
    return output
    

def get_database_replicas_list(alias, original, replicas):
    """Turns list of replicas into new database dicts.
    
    Args:
        alias (str): The alias of the writable database.
        original (dict): The write database configuration to model.
        replicas (list): Either the hostnames to model for, or a list of
            configs to send through 'get_database'.
    
    Returns:
        List of tuples of str, dict pairs.
    
    """
    # Go through the replicas list
    output = []
    num = 0
    for replica in replicas:
        
        # Replica will have a number attached to it
        num += 1
        replica_name = "%s-read%d" % (alias, num)
        
        # Just hostname?
        if isinstance(replica, str):
            temp = deepcopy(original)
            temp['HOST'] = replica
            output.append((replica_name, temp))
            continue
        
        # More parameters than just hostname
        if isinstance(replica, dict):
            temp = get_database(replica_name, original=original, override=replica)
            output.append(temp[0])
            continue
            
        # Illegal replica type
        raise TypeError("replica must be a string or dictionary")
        
    # Return!
    return output
    
    
def is_read_db(alias, original=None):
    """Tests whether or not the specified node is for read only."""
    regex = r'\-read[1-9]+\d*$'
    if original:
        regex = original + regex
    return bool(re.search(regex,alias))


def dbs_by_environment(environment, write_only=True):
    """
    Retrieve all database aliases that contain the given environment.
    
    Args:
        environment (str): The environment the databases must contain.
        write_only (Optional[bool]): Exclude any read-only databases.
    
    Returns:
        Set of aliases.
    
    """
    possible = set()
    for alias in settings.DATABASES:
        if write_only and is_read_db(alias):
            continue
        if environment in settings.DATABASES[alias]['ENVIRONMENTS']:
            possible.add(alias)
    return possible
    

def db_by_environment(environment):
    """Only returns one of the dbs_by_environment output."""
    possible = dbs_by_environment(environment)
    if not possible:
        return None
    return list(possible)[0]


def dict_fetchall(cursor):
    """Return all rows from a cursor as a dict.
    
    Source:
        https://docs.djangoproject.com/en/dev/topics/db/sql/#executing-custom-sql-directly
    
    """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_methods_from_class(cls):
    """Get a dict of methods from a given class.
    
    This function will ignore inherited methods or other attributes.
    
    Args:
        cls (class): The class to scan.
    
    Returns:
        dict: named methods.
    """
    output = {}
    attrs = dir(cls)
    for attr in attrs:
        value = getattr(cls,attr)
        original_cls = get_class_that_defined_method(value)
        if not original_cls:
            continue
        if original_cls == cls:
            output[attr] = value
    return output


def get_class_that_defined_method(meth):
    """Returns the class that created the given method.
    
    A helper function for finding class methods amongst a list of many
    methods. 
    
    Source:
        http://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3/25959545#25959545
    """
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
           if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__ # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        
        # Check to make sure the method has a "qualname"
        if not getattr(meth, '__qualname__', None):
            return None
        
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return None # not required since None would have been implicitly returned anyway