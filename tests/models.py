from django.contrib.gis.db import models as geo_models
from django.db import models
from django_schemas.models import Model as SchemaModel


class Test1AUser(SchemaModel, models.Model):
    name = models.CharField(max_length=100, unique=True, )
    db = models.CharField(max_length=63)
    
    def arbitrary_method(self):
        pass
    
    def get_child(self):
        cls = Test1BUser.set_db(db=self.db, schema='test1_b')
        return cls.objects.get(master_id=self.pk)
    
    class Meta:
        db_environment = 'test1-a'


class Test1BUser(SchemaModel, models.Model):
    master_id = models.BigIntegerField(unique=True)
    color = models.CharField(max_length=100, default="grey")
    
    class Meta:
        db_environment = 'test1-b'


class Test1BCar(SchemaModel, models.Model):
    user = models.ForeignKey(Test1BUser)
    color = models.CharField(max_length=100, default="blue")
    
    class Meta:
        db_environment = 'test1-b'


class Test1BLocation(SchemaModel, geo_models.Model):
    coord = geo_models.PointField()
    
    class Meta:
        db_environment = 'test1-b'