"""
Custom authentication backend for email-based authentication
"""
from django.contrib.auth.backends import ModelBackend
from .models import User


class EmailAuthBackend(ModelBackend):
    """
    Custom authentication backend that allows login with email instead of username
    """
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        # Support both 'email' and 'username' parameters
        email = email or username
        
        if email is None or password is None:
            return None
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            User().set_password(password)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
    
    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None


