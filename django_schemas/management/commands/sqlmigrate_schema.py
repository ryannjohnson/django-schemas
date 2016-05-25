from django.core.management.base import BaseCommand, CommandError

from ...migrations import sqlmigrate


class Command(BaseCommand):
    """Migrate a schema."""
    
    help = 'Migrates a database and schema'
    
    def add_arguments(self, parser):
        parser.add_argument('app_label',
                type=str,
                help="which Django app to generate for")
        parser.add_argument('migration_name',
                type=str,
                help="which migration to generate for")
        parser.add_argument('--database',
                dest='database',
                default=None,
                help="database to use for migration")
        parser.add_argument('--schema',
                dest='schema',
                default=None,
                help="schema to use for migration")
        parser.add_argument('--environment',
                dest='environment',
                default=None,
                help="environment to migrate")
        parser.add_argument('--backwards',
                dest='backwards',
                default=None,
                help="sql for unapplying a migration")
        
    def handle(self, *args, **options):
        """Migrate the secondary database and schema.
        
        Args:
            **options:
                app_label (str): Django app to generate from.
                migration_name (str): Migration to generate from.
                database (Optional[str]): Database to migrate.
                schema (Optional[str]): Schema to migrate.
                environment (Optional[str]): Environment to migrate.
                backwards (Optional[bool]): Unapply migration?
        
        """
        # Make sure we have what we need
        app_label = options.get('app_label')
        migration_name = options.get('migration_name')
        db = options.get('database')
        schema = options.get('schema')
        environment = options.get('environment')
        backwards = options.get('backwards')
        
        # Do the migration
        sqlmigrate(
                app_label=app_label,
                migration_name=migration_name,
                db=db,
                schema=schema,
                environment=environment,
                backwards=backwards,
                **options)