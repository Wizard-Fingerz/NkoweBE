from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from account.models import CustomUser



class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            user = CustomUser.objects.get(
                Q(username__iexact=username) |
                Q(email__iexact=username)
            )
        except CustomUser.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
