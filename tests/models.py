from django_schemas import models


# 
# Test 1
# 

class Test1AUserMeta:
    db_environment = 'test1-a'

class Test1AUser(models.Model):
    name = models.CharField(max_length=100, unique=True, )
    db = models.CharField(max_length=63)
    
    class Meta(Test1AUserMeta):
        pass


class Test1BUserMeta:
    db_environment = 'test1-b'

class Test1BUser(models.Model):
    master_id = models.BigIntegerField(unique=True)
    favorite_color = models.CharField(max_length=100, default="grey")
    
    class Meta(Test1BUserMeta):
        pass
