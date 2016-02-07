from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.test import TestCase
from django_schemas.migrations import flush, migrate
from django_schemas.utils import dict_fetchall
import json
from tests.models import Test1AUser, Test1BCar, Test1BUser


class Test1(TestCase):
    
    def test_migration_structure(self):
        """
        The focus here is to create migrations from the test models, migrate
        them across different environments and databases, and then test the
        `set_db` methods of each model.
        """
        # Flush in the event of errors
        flush(db='db1', schema='test1_a')
        flush(db='db1', schema='test1_b')
        flush(db='db2', schema='test1_b')
        
        # Do the migrations for each environment
        migrate(db='db1', environment='test1-a', big_ints=True)
        migrate(db='db1', schema='test1_b', environment='test1-b', big_ints=False)
        migrate(db='db2', schema='test1_b', environment='test1-b', big_ints=True)
        
        # Gather the results afterwards
        sql = """
            SELECT
                *
            FROM information_schema.tables
            WHERE 
                table_schema=%(schema)s
        """
        c1 = connections['db1'].cursor()
        c1.execute(sql,{'schema':'test1_a'})
        a_results = dict_fetchall(c1)
        c1.execute(sql,{'schema':'test1_b'})
        b1_results = dict_fetchall(c1)
        c2 = connections['db2'].cursor()
        c2.execute(sql,{'schema':'test1_b'})
        b2_results = dict_fetchall(c2)
        
        # Test and see that each schema has the correct tables
        a_tables = ['django_migrations','tests_test1auser']
        b_tables = ['django_migrations','tests_test1buser','tests_test1bcar']
        a_collected = [a["table_name"] for a in a_results]
        b1_collected = [a["table_name"] for a in b1_results]
        b2_collected = [a["table_name"] for a in b2_results]
        for a in a_tables:
            self.assertTrue(a in a_collected)
        for a in b_tables:
            self.assertTrue(a in b1_collected)
            self.assertTrue(a in b2_collected)
        self.assertTrue(len(a_tables) == len(a_collected))
        self.assertTrue(len(b_tables) == len(b1_collected))
        self.assertTrue(len(b_tables) == len(b2_collected))
        
        # Make a row for each table
        user1a = Test1AUser.auto_db().objects.create(name="garfield1", db="db1")
        user2a = Test1AUser.auto_db().objects.create(name="garfield2", db="db2")
        user1b = Test1BUser.set_db("db1","test1_b").objects.create(
                master_id=user1a.pk, color="blue")
        user2b = Test1BUser.set_db("db2","test1_b").objects.create(
                master_id=user2a.pk, color="green")
        
        # Test the arbitrary method transferal
        user1a.arbitrary_method()
        
        # Retrieve rows
        u1a = Test1AUser.auto_db().objects.get(name="garfield1")
        u2a = Test1AUser.inherit_db(u1a).objects.get(pk=2)
        u1b = u1a.get_child()
        u2b = Test1BUser.set_db("db2","test1_b").objects.get(master_id=u2a.pk)
        
        # Test them against one another
        self.assertTrue(u1b.master_id == u1a.pk)
        self.assertTrue(u2b.master_id == u2a.pk)
        
        # Try adding a car to the mix
        c1b1 = Test1BCar.inherit_db(u1b).objects.create(user=u1b, color="green")
        c1b2 = u1b.test1bcar_set.create(color="yellow")
        
        # Try to mix schemas (and fail)
        c2b3 = Test1BCar.inherit_db(u2b).objects.create(user=u1b, color="orange")
        
        # Clean up after ourselves
        flush(db='db1', schema='test1_a')
        flush(db='db1', schema='test1_b')
        flush(db='db2', schema='test1_b')