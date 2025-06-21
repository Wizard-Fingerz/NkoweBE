from django.db.models.signals import post_save, post_migrate
from django.db import transaction
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from account.models import CustomUser
from .models import UserType
from chat_app.models import ChatRoom

@receiver(post_save, sender=CustomUser)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        if instance.id is None:
            print("User  ID is None, cannot create token")
            return
        try:
            user = CustomUser.objects.get(id=instance.id)
            if user:
                Token.objects.create(user=user)
            else:
                print("User  does not exist, cannot create token")
        except Exception as e:
            print(f"Error creating token: {e}")

@receiver(post_save, sender=CustomUser)
def create_user_chat_room(sender, instance=None, created=False, **kwargs):
    if created and instance:
        room, room_created = ChatRoom.objects.get_or_create(
            name=f"{instance.username}'s Room"
        )
        room.participants.add(instance)

@receiver(post_migrate)
def create_user_types(sender, **kwargs):
    if sender.name == 'account':
        initial_types = [
            ('Admin', 'System administrator with full access'),
            ('Student', 'Student user with learning access'),
            ('Institution Owner', 'Owner or manager of an educational institution'),
            ('Tutor', 'Individual providing one-on-one tutoring'),
            ('Moderator', 'Content and community moderator'),
            ('Teacher', 'Educational institution teacher'),
            ('Counselor', 'Educational guidance counselor'),
            ('Administrator', 'Institution administrator'),
            ('Librarian', 'Educational resource manager'),
            ('IT Staff', 'Technical support staff'),
            ('Alumni', 'Former student'),
            ('Guest Lecturer', 'Occasional teaching staff'),
            ('Mentor', 'Student guide and mentor'),
            ('Research Partner', 'Research collaboration partner'),
            ('Government Agency', 'Government education representative'),
            ('Other', 'Other user type')
        ]
        
        for name, description in initial_types:
            UserType.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'is_active': True
                }
            )

@receiver(post_migrate)
def create_default_user_types(sender, **kwargs):
    if sender.name == 'account':
        default_types = [
            {
                'name': 'Student',
                'description': 'A student user who can enroll in courses and access learning materials.'
            },
            {
                'name': 'Institution Owner',
                'description': 'An institution owner who can manage their educational institution.'
            },
            {
                'name': 'Teacher',
                'description': 'A teacher who can create and manage courses.'
            },
            {
                'name': 'Administrator',
                'description': 'An administrator who can manage the platform.'
            }
        ]

        for type_data in default_types:
            UserType.objects.get_or_create(
                name=type_data['name'],
                defaults={
                    'description': type_data['description'],
                    'is_active': True
                }
            )