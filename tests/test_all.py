from tests.models import PrimaryUser, SecondaryThing


def test_sample():
    assert True

def test_all():
    """Test the entire extension.
    
    Since the tests all have to do with analyzing what's present on the
    database, it can't be a series of seperate tests. Instead, we have
    to migrate and then run multiple tests.
    """
    assert False