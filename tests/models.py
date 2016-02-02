from django_schemas import models


class PrimaryUserMeta:
	db_environment = 'primary'

class PrimaryUser(models.Model):
	name = models.CharField(max_length=100, unique=True, )
	db = models.CharField(max_length=63)
	
	class Meta(PrimaryUserMeta):
		pass


class SecondaryThingsMeta:
	db_environment = 'secondary'

class SecondaryThings(models.Model):
	name = models.CharField(max_length=100, default="untitled")