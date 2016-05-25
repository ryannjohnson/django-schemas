from django.core.management.base import BaseCommand, CommandError

from ...migrations import migrate


class Command(BaseCommand):
    """Generate sql for a schema migration."""
    
    help = 'Generate sql for a schema migration.'
    
    def add_arguments(self, parser):
        parser.add_argument('database',
                type=str,
                help="database to use for migration")
        parser.add_argument('--schema',
                dest='schema',
                default=None,
                help="schema to use for migration")
        parser.add_argument('--environment',
                dest='environment',
                default=None,
                help="environment to migrate")
        parser.add_argument('--big-ints',
                dest='big_ints',
                default=None,
                help="environment to migrate")
        
    def handle(self, *args, **options):
        """Migrate the secondary database and schema.
        
        Args:
            **options:
                database (str): Database to migrate.
                schema (Optional(str)): Schema to migrate.
                environment (Optional(str)): Environment to migrate.
        
        """
        # Make sure we have what we need
        db = options.get('database')
        schema = options.get('schema')
        environment = options.get('environment')
        big_ints = options.get('big_ints')
        
        # Do the migration
        migrate(
                db=db,
                schema=schema,
                environment=environment,
                big_ints=big_ints)