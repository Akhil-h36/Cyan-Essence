from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        try:
            # Try to find a user by email
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            # Return None if no user is found
            return None

        # Check password
        if user.check_password(password):
            return user
        
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None