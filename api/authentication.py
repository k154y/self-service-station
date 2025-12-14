from rest_framework.authentication import SessionAuthentication # Import DRF's base class
from service.models import User  # Import the User model

class CustomSessionAuthentication(SessionAuthentication):
    """
    Tells DRF to validate the user based on your custom session key ('user_id').
    This is what makes the API work with your current Django login system.
    """
    def authenticate(self, request):
        user_id = request.session.get('user_id')
        
        if user_id:
            try:
                # Retrieve the User instance using your custom ID
                user = User.objects.get(user_id=user_id)
                # DRF requires a (user, auth) tuple; None for 'auth' means session auth
                return (user, None)
            except User.DoesNotExist:
                return None
        return None