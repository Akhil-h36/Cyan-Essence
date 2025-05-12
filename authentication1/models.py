from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
import uuid
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)

        if 'refferal_code' not in extra_fields or not extra_fields['refferal_code']:
            extra_fields['refferal_code'] = str(uuid.uuid4())[:8].upper()
            
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class usertable(AbstractBaseUser, PermissionsMixin):
    # Phone number validation
    username = None
    phone_regex = RegexValidator(
        regex=r'^[5-9]\d{9}$', 
        message="Phone number must be a valid 10-digit Indian mobile number starting with 6-9."
    )

    # Email field with explicit parameters
    email = models.EmailField(
        unique=True, 
        max_length=255, 
        verbose_name='Email Address',
        db_column='user_email'  # Explicitly specify column name
    )

    firstname = models.CharField(
        max_length=100, 
        verbose_name='First Name'
    )
    
    lastname = models.CharField(
        max_length=100,  
        verbose_name='Last Name'
    )

    phonenumber = models.CharField(
        max_length=10, 
        unique=True,
        validators=[phone_regex],
        verbose_name='Phone Number'
    )

    refferal_code = models.CharField(
        max_length=10, 
        unique=True,
        blank=True,
        verbose_name='Referral Code',
        null=True,
    )


    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    # Required fields for custom user model
    is_active = models.BooleanField(default=True)
   
    date_joined = models.DateTimeField(default=timezone.now)

    # Specify email as the unique identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstname', 'lastname', 'phonenumber']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.firstname} {self.lastname} ({self.email})"

    def get_full_name(self):
        return f"{self.firstname} {self.lastname}"

    def get_short_name(self):
        return self.firstname

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']