from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from account.models import CustomUser

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