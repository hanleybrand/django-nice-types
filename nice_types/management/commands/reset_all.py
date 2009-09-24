from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = """
Runs reset for all apps"""
    
    def handle_noargs(self, **options):
        from django.db.models import loading
        from django.core.management import call_command

        for app in loading.get_apps():
            call_command('reset', app.__name__.split('.')[-2], interactive=False)
        call_command('syncdb')


