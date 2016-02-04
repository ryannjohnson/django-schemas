from django_schemas import models


# 
# Test 1
# 

class Test1AUserActions:
    def b_user(self):
        m = Test1BUser.set_db(self.db_name, self.schema_name).objects
        return m.get(master_id=self.pk)

class Test1AUserMeta:
    db_environment = 'test1-a'

class Test1AUser(models.Model, Test1AUserActions):
    name = models.CharField(max_length=100, unique=True, )
    db = models.CharField(max_length=63)
    
    class Meta(Test1AUserMeta):
        pass


class Test1BUserMeta:
    db_environment = 'test1-b'

class Test1BUser(models.Model):
    master_id = models.BigIntegerField(unique=True)
    color = models.CharField(max_length=100, default="grey")
    
    class Meta(Test1BUserMeta):
        pass
