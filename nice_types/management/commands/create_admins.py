from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = """
Creates admin accounts for the admins located in settings.ADMINS"""
    
    def handle_noargs(self, **options):
        from django.conf import settings
        from django.contrib.auth.models import User, Permission
        from members.models import Member

        for name, email in settings.ADMINS:
            names = name.split(" ", 1)
            first_name = names[0]
            last_name = names[1] if len(names) == 2 else ""
            
            try:
                u = Member.objects.get(email=email)
                print "Updating %s" % email
            except Member.DoesNotExist:
                print "Creating %s" % email
                u = Member.objects.create_member(first_name, last_name, email, password=email)
            u.is_staff = True
            u.is_superuser = True
            u.save()
            u.user_permissions.add(*Permission.objects.all())

