from django.test import TestCase, TransactionTestCase


class SampleTestClass(TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_sample(self):
        self.assertTrue(True)

def test_all():
    """Test the entire extension.
    
    Since the tests all have to do with analyzing what's present on the
    database, it can't be a series of seperate tests. Instead, we have
    to migrate and then run multiple tests.
    """
    pass