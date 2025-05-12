from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

# class EmailAuthBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         try:
#             user = User.objects.get(email=username)
#             if user.check_password(password):
#                 return user
#         except User.DoesNotExist:
#             return None
# from django.contrib.auth.models import User
# from django.contrib.auth.backends import ModelBackend

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            if request.path.startswith('/adminapp/'):
                user = User.objects.filter(email=username, is_superuser=True).first()
            else:
                # For regular users, just get the first match
                user = User.objects.filter(email=username).first()
            
            if user and user.check_password(password):
                return user
            return None
        except Exception:
            return None