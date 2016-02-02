from django.conf import settings
from django.core.management import call_command
from django_schemas.migrations import migrate
from tests.models import PrimaryUser, SecondaryThing


def test_1():
    """
    The focus here is to create migrations from the test models, migrate
    them across different environments and databases, and then test the
    `set_db` methods of each model.
    """
    # Create the migrations
    call_command('makemigrations','tests')
    
    # Do the migrations for each environment
    migrate(db='db1', environment='test1-a', big_ints=False)
    migrate(db='db2', schema='test1-b', environment='test1-b', big_ints=True)
    
    