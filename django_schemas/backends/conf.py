

SCHEMA_NAME = None
"""Force a schema name when using a database.

Hacky solution to not finding a place to inject a schema name
into migrations.
"""

ADDITIONAL_SCHEMAS = []
"""When forcing a schema, include additional search schemas.

Adds to the hacky solution of migrating across multiple schemas. This
allows the current schema to access resources from other schemas, for
example Postgis on the 'public' schema will need to be accessible for
geospacial columns, indexes, etc.
"""

ENVIRONMENT_NAME = None
"""Force an environment name when using a database.

Hacky solution to not finding a place to route migrations to their
appropriate schemas.
"""