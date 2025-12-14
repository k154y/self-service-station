from rest_framework.authentication import SessionAuthentication, TokenAuthentication, BaseAuthentication
from rest_framework.authtoken.models import Token
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


class HybridAuthentication(BaseAuthentication):
    """
    Hybrid authentication that supports both session-based and token-based authentication.
    Tries token authentication first, then falls back to session authentication.
    """
    def authenticate(self, request):
        # Try token authentication first
        token_auth = TokenAuthentication()
        token_result = token_auth.authenticate(request)
        if token_result:
            user, token = token_result
            return token_result
        
        # Fall back to session authentication
        session_auth = CustomSessionAuthentication()
        session_result = session_auth.authenticate(request)
        if session_result:
            return session_result
        
        return None