from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Creates a test user for debugging purposes'

    def handle(self, *args, **options):
        username = os.getenv('TEST_USERNAME')
        password = os.getenv('TEST_PASSWORD')
        
        if not username or not password:
            self.stdout.write(self.style.ERROR('Missing TEST_USERNAME/TEST_PASSWORD in environment'))
            return

        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={'role': 'admin'}
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'User {username} created successfully'))
        else:
            self.stdout.write('User elzeny already exists')
        
        # Verify password
        check_user = CustomUser.objects.get(username='elzeny')
        self.stdout.write(f'Password validation: {check_user.check_password("123")}')