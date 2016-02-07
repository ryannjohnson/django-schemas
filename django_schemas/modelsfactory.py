import collections
from copy import deepcopy
from django.conf import settings
from django_schemas.utils import get_methods_from_class
import json
import re
from urllib.parse import urlencode


CLONABLE_META_ATTRS = ['db_environment']
"""The _meta attributes that should be copied from the parent.

This allows users to create models with Meta classes inside as usual,
instead of depending on inheritance for clones to get the same
attributes.
"""


EXISTING_MODEL_CLONES = {}
"""Holds existing classes with specific options.

Since each new class is always global and needs a unique name each
time, they'll be stored here and referenced whenever needed again.
If nothing else, this is a model clone cache.

Looks like:
    {
        'database_name': {
            'schema_name': {
                'ClassName_serialized-extras': ClonedClass,
            },
        },
    }
"""


def clone_model(model_cls, db=None, schema=None, *args, **kwargs):
    """Create a clone of a Django model for a specific db and schema.
    
    Cloned models are registered with Django as completely unique from
    their originals. Their related fields will also be updated with
    models that reflect the chosen db and schema.
    
    Args:
        db (str): Alias of database to use for this model.
        schema (str): Schema/namespace for this model.
    
    Returns:
        Class containing the meta information included.
    
    """
    # Prepare some variables for later class instantiation
    schema_friendly_table = model_cls._meta.db_table
    table_name = model_cls._meta.db_table
    if getattr(model_cls._meta, 'table_name', None):
        schema_friendly_table = model_cls._meta.table_name
        table_name = model_cls._meta.table_name
    if schema:
        schema_friendly_table = '%s\".\"%s' % (schema, schema_friendly_table)
    
    # Spit out the cloned model
    return get_model(model_cls, options={
        'db_name': db,
        'db_table': schema_friendly_table,
        'schema_name': schema,
        'table_name': table_name,
    }, db=db, schema=schema)


def get_model(model_cls, options={}, **kwargs):
    """
    Derive all necessary information from the source model definition to
    create a clone with whatever Meta adjustments desired.
    
    Args:
        model_cls (class): The class to clone.
        options (dict): The meta fields to inject into the new clone.
        
    Returns:
        Class definition clone of the input model.
    
    """
    # Check for existing first
    serial_name, existing_cls = _get_cloned_model(model_cls, options)
    if existing_cls:
        return existing_cls
    
    # Start the meta dictionary
    meta_options = {}
    
    # Import from the source Meta class by explicit keys
    clonable_meta = getattr(settings,'CLONABLE_META_ATTRS',CLONABLE_META_ATTRS)
    for attr in clonable_meta:
        meta_options[attr] = getattr(model_cls._meta, attr, None)
    
    # Now add the supplied options (to override the meta)
    for field in options:
        meta_options[field] = options[field]
    
    # Convert the fields into the proper format
    fields = _get_model_fields(model_cls)
    
    # Get any methods that might belong to this model alone
    methods = get_methods_from_class(model_cls)
    
    # Make the new model based off the old one
    new_model = create_model(
            name=serial_name,
            fields=fields,
            app_label=model_cls._meta.app_label,
            module=model_cls.__module__,
            options=meta_options,
            bases=model_cls.__bases__,
            attrs=methods,
            **kwargs)
    
    # Save this model for use while this process is alive
    _set_cloned_model(new_model)
    
    # Return the cloned model
    return new_model


def _get_cloned_model(model_cls, options={}):
    """
    Generates the model name and looks for an existing declaration of
    the requested model.
    
    Args:
        model_cls (str): Original class passed to this model.
        options (dict): Meta data attributes to pass along.
        
    Returns:
        Tuple containing two elements, including the model name as a
            string, and the existing class if present. None otherwise.
    
    """
    # Holds the references to existing clones
    global EXISTING_MODEL_CLONES
    
    # Make our own version of options
    options_temp = deepcopy(options)
    db_name = str(options_temp['db_name'])
    schema_name = str(options_temp['schema_name'])
    del options_temp['table_name']
    del options_temp['db_table']
    del options_temp['db_name']
    del options_temp['schema_name']
    options_temp = collections.OrderedDict(sorted(options_temp.items()))
    
    # Make the serial name for the model
    matches = re.match(r'^(.+?)__',model_cls.__name__)
    if not matches:
        match = model_cls.__name__
    else:
        match = matches.group(1)
    serial_name = match + '__'
    regex_sub = re.compile(r'[^a-zA-Z0-9_]')
    serial_name += regex_sub.sub(r'', db_name) + '__'
    serial_name += regex_sub.sub(r'', schema_name) + '__'
    for key, value in options_temp.items():
        serial_name += regex_sub.sub(r'',str(key))
        serial_name += regex_sub.sub(r'', str(value))
        serial_name += '__'
    
    # Check for the class in the existing pile
    existing_clone = None
    if db_name not in EXISTING_MODEL_CLONES:
        EXISTING_MODEL_CLONES[db_name] = {}
    if schema_name not in EXISTING_MODEL_CLONES[db_name]:
        EXISTING_MODEL_CLONES[db_name][schema_name] = {}
    eds = EXISTING_MODEL_CLONES[db_name][schema_name]
    if serial_name in eds:
        existing_clone = eds[serial_name]
    
    # Return
    return serial_name, existing_clone


def _set_cloned_model(model_cls):
    """Save the created model in the dict stack.
    
    Args:
        model_cls (class): The created model class.
    
    """
    # Setup some variables
    global EXISTING_MODEL_CLONES
    db_name = model_cls._meta.db_name
    schema_name = model_cls._meta.schema_name
    cls_name = model_cls.__name__
    
    # Plug in the reference
    if db_name not in EXISTING_MODEL_CLONES:
        EXISTING_MODEL_CLONES[db_name] = {}
    if schema_name not in EXISTING_MODEL_CLONES[db_name]:
        EXISTING_MODEL_CLONES[db_name][schema_name] = {}
    EXISTING_MODEL_CLONES[db_name][schema_name][cls_name] = model_cls


def _get_class_attrs(cls):
    """Get the list of all attributes of a class.
    
    Args:
        cls (class): Class to get attributes of.
        
    Returns:
        List of attribute names.
    
    Source:
        http://stackoverflow.com/questions/191010/how-to-get-a-complete-list-of-objects-methods-and-attributes#10313703
    
    """
    attrs = dir(cls)
    if hasattr(cls, '__bases__'):
        for base in cls.__bases__:
            attrs = attrs + _get_class_attrs(base)
    return attrs


def _get_model_fields(model_cls):
    """Turns a model's list of fields into a dictionay of fields.
    
    Args:
        model_cls (class): Has the meta attribute 'fields'.
    
    Returns:
        dict: named fields.
    
    """
    fields = {}
    
    # Start by getting the fields from all the bases
    for base in model_cls.__bases__:
        fields.update(_get_model_fields(base))
    
    # Check to make sure the input class has fields
    if not getattr(model_cls, '_meta', None):
        return fields
    if not getattr(model_cls._meta, 'fields', None):
        return fields
    
    # Start collecting
    i = 0
    for field in model_cls._meta.fields:
        field_name = str(field).split('.')[-1]
        fields[field_name] = model_cls._meta.fields[i]
        i += 1
    return fields


def create_model(
        name, fields=None, app_label='', module='', options=None,
        admin_opts=None, bases=None, **kwargs):
    """Create specified model from scratch at runtime.
    
    This is a generic model creation tool for Django. Its foremost
    advantage over normal inheritance is its ability to own its own
    roots in the Django application.
    
    Args:
        name (str): Name of the model that gets produced.
        fields (dict): Fields to add to the model.
        app_label (str): What app is this model a part of?
        module (str): What module is this app apart of?
        options (dict): Fields to add to the Meta class of the model.
        admin_opts (dict): Fields to add to the Admin class of the model.
        bases (tuple): The bases for the original class.
    
    Returns:
        Class definition of model.
    
    Source:
        https://code.djangoproject.com/wiki/DynamicModels
    
    """
    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.items():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}
    
    # Add in any additional methods or attributes to the class
    attrs.update(kwargs.get('attrs', {}))
    
    # Add in any fields that were provided
    if fields:
        if bases:
            
            # Avoid clashes between fields that were inherited
            fields_to_remove = set()
            for base in bases:
                for field in fields:
                    base_fields = _get_model_fields(base)
                    if field in base_fields:
                        fields_to_remove.add(field)
            for field in fields_to_remove:
                fields.pop(field, None)
        
        # Clone any related fields
        for field in fields:
            fields[field] = clone_related_field(
                    field_obj=fields[field], db=kwargs.get('db', None),
                    schema=kwargs.get('schema', None),)
        
        # Add the fields
        attrs.update(fields)
    
    # Create the class, which automatically triggers ModelBase processing
    model = type(name, bases, attrs)
    
    # Create an Admin class if admin options were provided
    if admin_opts is not None:
        class Admin(admin.ModelAdmin):
            pass
        for key, value in admin_opts:
            setattr(Admin, key, value)
        admin.site.register(model, Admin)

    return model


def clone_related_field(field_obj, db, schema):
    """Clone an existing relationship field.
    
    For new models based on databases and schemas, the related fields
    involved will also need to be created. This allows for proper
    implicit validation, as well as proper model fetching.
    
    If the field isn't a relationship field, then just return the input
    field object.
    
    Args:
        field_obj (object): Any field object.
        db (str): Alias of the database to be used.
        schema (str): Name of the schema to be used.
    
    Returns:
        object: Field object.
    
    """
    
    # Is it a relationship field?
    if not field_obj.rel:
        return field_obj
    
    # Get the appropriate class to inject
    new_model_cls = field_obj.rel.to.set_db(db=db, schema=schema)
    
    # Create the object for this field
    new_field_obj = field_obj.__class__(new_model_cls)
    
    # Transfer over all the field attributes
    attrs = field_obj.__dict__.keys()
    for attr in attrs:
        value = getattr(field_obj, attr)
        if (isinstance(value, list) or
                isinstance(value, dict) or
                isinstance(value, set)):
            value = deepcopy(value)
        setattr(new_field_obj, attr, value)
    
    # Make sure this new field reflects the correct target
    new_field_obj.model = new_model_cls
    new_field_obj.rel.model = new_model_cls
    
    # Return the fresh field
    return new_field_obj