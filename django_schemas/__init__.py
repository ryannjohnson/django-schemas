from django.conf import settings

from .utils import DotDict


# Lookup table for certain types of environments

if settings.get('DATABASE_ENVIRONMENT_TYPES', None):
    ENVIRONMENTS = DotDict(settings.get('DATABASE_ENVIRONMENT_TYPES'))
else:
    ENVIRONMENTS = DotDict({
        'primary': 'primary',
        'secondary': 'secondary',
    })