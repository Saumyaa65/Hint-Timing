import os
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from clerk_backend_api import Clerk
from django.contrib.auth.models import User

# We'll import UserProfile inside the method to avoid circular imports if models.py imports this
clerk_client = Clerk(bearer_auth=os.environ.get('CLERK_SECRET_KEY'))

class ClerkAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        
        try:
            # For a production app, verify the JWT properly using python-jose and JWKS.
            # Here we'll use a simplified check or the Clerk API client to get user details.
            # The token is the session token.
            import jwt
            
            # Decode without verification just to extract the 'sub' (user ID)
            # In a real app, verify signature against Clerk's JWKS
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            clerk_user_id = unverified_payload.get('sub')
            
            if not clerk_user_id:
                raise AuthenticationFailed('Invalid token payload')
                
            # Find or create local user
            user, created = User.objects.get_or_create(username=clerk_user_id)
            
            from .models import UserProfile
            # Find or create UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'clerk_id': clerk_user_id})
            
            return (user, token)
            
        except Exception as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
