### django-schemas 0.2.0

- `django_schemas.models` no longer imports `django.db.models.*`.
  - Models must now inherit from both `django_schemas.models.Model` and `django.db.models.Model`.
  - Allows schema-enabled models to instead inherit from other packages, eg. `django.contrib.gis.db.Model`.