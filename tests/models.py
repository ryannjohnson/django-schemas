from django_schemas import models


# 
# Test 1
# 

class Test1AUser(models.Model):
    name = models.CharField(max_length=100, unique=True, )
    db = models.CharField(max_length=63)
    
    def arbitrary_method(self):
        pass
    
    class Meta:
        db_environment = 'test1-a'

class Test1BUser(models.Model):
    master_id = models.BigIntegerField(unique=True)
    color = models.CharField(max_length=100, default="grey")
    
    class Meta:
        db_environment = 'test1-b'
