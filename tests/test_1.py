from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.test import TestCase
from django_schemas.migrations import flush, migrate
from django_schemas.utils import dict_fetchall
import json
from tests.models import Test1AUser, Test1BUser


class Test1(TestCase):
    
    def test_1(self):
        """
        The focus here is to create migrations from the test models, migrate
        them across different environments and databases, and then test the
        `set_db` methods of each model.
        """
        # Create the migrations
        call_command('makemigrations','tests')
        
        # Do the migrations for first environment
        migrate(db='db1', environment='test1-a', big_ints=False)
        c1 = connections['db1'].cursor()
        c1.execute("""
            SELECT
                *
            FROM information_schema.tables
            WHERE 
                table_schema=%(schema)s
        """,{'schema':'test1_a'})
        a_results = dict_fetchall(c1)
        with open('/var/www/projects/ryannjohnson/django-schemas/results1a.txt', 'w') as f:
            f.write(json.dumps(a_results, indent=4))
        
        migrate(db='db2', schema='test1_b', environment='test1-b', big_ints=True)
        c2 = connections['db2'].cursor()
        c2.execute("""
            SELECT
                *
            FROM information_schema.tables
            WHERE 
                table_schema=%(schema)s
        """,{'schema':'test1_b'})
        b_results = dict_fetchall(c1)
        with open('/var/www/projects/ryannjohnson/django-schemas/results1b.txt', 'w') as f:
            f.write(json.dumps(b_results, indent=4))
        
        # Test and see that each schema has the correct tables
        a_tables = ['django_migrations','tests_test1auser']
        b_tables = ['django_migrations','tests_test1buser']
        a_collected = [a["table_name"] for a in a_results]
        b_collected = [a["table_name"] for a in b_results]
        for a in a_tables:
            self.assertTrue(a in a_collected)
        for a in b_tables:
            self.assertTrue(a in b_collected)
        
        
        # Wrap up with a flush
        flush(db='db1', schema='test1_a')
        flush(db='db2', schema='test1_b')