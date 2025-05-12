from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.email:
            raise ValidationError("Email is required")
        user.username = user.email  # Set username to email if needed
        return user

class CustomAccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        user.username = user.email  # Use email as username