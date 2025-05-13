from django.shortcuts import render,redirect
from django.contrib.auth.hashers import make_password
import random
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from adminapp.models import Wallet,WalletTransaction
import re
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.contrib.messages import get_messages
from . models import usertable 
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
import logging
from decimal import Decimal
import uuid
logger = logging.getLogger(__name__)


@never_cache
def userlogin(request):
    if request.user.is_authenticated:
        return redirect('home')

    context = {
        'google_login_available': SocialApp.objects.filter(provider='google').exists()
    }

    if request.method == "POST":
        email = request.POST.get('useremail')
        password = request.POST.get('userpass')

        print(f"Login attempt for email: {email}")

        # Validate input
        if not email or not password:
            messages.error(request, "Please provide both email and password.")
            return render(request, 'authentication1/userlogin.html')

        # Use the custom EmailBackend for authentication
        user = authenticate(request, email=email, password=password)
        print(f"Authentication result: {user}")

        if user is not None:
            # Check if the user is active and staff status
            if user.is_active:
                print(f"User active status: {user.is_active}")
                login(request, user)
                messages.success(request, f"Successfully logged in. Welcome, {user.firstname}!")
                return redirect('home')
            else:
                messages.error(request, "Your account is not active. Please contact support.")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'authentication1/userlogin.html',context)


def validate_password_strength(password):
    """
    Validate password strength:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        return False
    
    if not re.search(r'[a-z]', password):
        return False
    
    if not re.search(r'\d', password):
        return False
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True

def validate_phone_number(phone):
    """
    Validate phone number:
    - Only digits
    - Exactly 10 digits
    - Starts with 5-9
    """
    if not phone.isdigit():
        return False
    
    if len(phone) != 10:
        return False
    
    
    if not phone[0] in '56789':
        return False
    
    return True

def usersignup(request):
    if request.method == "POST":
        # Sanitize and strip input
        fname = request.POST.get('fname', '').strip()
        lname = request.POST.get('lname', '').strip()
        email = request.POST.get('email', '').strip().lower()  # Normalize email
        phone = request.POST.get('pnumber', '').strip()
        pass1 = request.POST.get('epass', '')
        pass2 = request.POST.get('cpass', '')
        referral_code = request.POST.get('referralcode', '').strip()
        
        errors = []

        # Name validation
        if not fname or len(fname) < 2:
            errors.append("First name must be at least 2 characters long.")
        
        if not lname or len(lname) < 1:
            errors.append("Last name must be at least 1 character long.")

        # Email validation
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Invalid email address.")
        
        # Check if email already exists
        if usertable.objects.filter(email=email).exists():
            errors.append("Email is already registered.")

        # Phone number validation
        if not validate_phone_number(phone):
            errors.append("Invalid phone number. Must be a 10-digit number starting with 5-9.")

        # Password validation
        if pass1 != pass2:
            errors.append("Passwords do not match.")
        
        password_error = """Password must:
        - Be at least 8 characters long
        - Contain at least one uppercase letter
        - Contain at least one lowercase letter
        - Contain at least one number
        - Contain at least one special character"""
        
        if not validate_password_strength(pass1):
            errors.append(password_error)

        referring_user = None
        if referral_code:
            try:
                referring_user = usertable.objects.get(refferal_code=referral_code)
            except usertable.DoesNotExist:
                errors.append("Invalid referral code.")
        
        if errors:
            return render(request, 'authentication1/usersignup.html', {
                'errors': errors,
                'fname': fname,
                'lname': lname,
                'email': email,
                'phone': phone,
                'referralcode': referral_code 
            })

        # Create user if all validations pass
        try:
            # Use create_user method from CustomUserManager
            signup_obj = usertable.objects.create_user(
                email=email,
                password=pass1,
                firstname=fname,
                lastname=lname,
                phonenumber=phone,
                is_active=False,
                referred_by=referring_user
            )

            Wallet.objects.create(user=signup_obj)

            if referring_user:
                try:
                    referring_wallet = Wallet.objects.get(user=referring_user)
                    REFERRAL_BONUS = Decimal('1000.00')
                    referring_wallet.balance += REFERRAL_BONUS
                    referring_wallet.save()
                    
                    WalletTransaction.objects.create(
                        wallet=referring_wallet,
                        transaction_type='add',
                        transaction_amount=REFERRAL_BONUS,
                        description=f"Referral bonus from {signup_obj.email}"
                    )
                except Exception as wallet_error:
                    logger.error(f"Wallet referral error: {wallet_error}")

            # Generate OTP
            otp = f"{random.randint(0, 9999):04d}"
            
            # Store OTP in session
            request.session['otp'] = otp
            request.session['email'] = email
            request.session['signup_user_id'] = signup_obj.id
            request.session.save()  # Explicitly save session
            
            print(f"Generated OTP for {email}: {otp}")
            logger.debug(f"Session data stored - OTP: {otp}, Email: {email}, User ID: {signup_obj.id}")
           
            subject = "Your OTP for Signup Verification"
            message = f"Hello {fname},\n\nYour OTP for account verification is: {otp}\n\nDo not share it with anyone."
            
            try:
                send_mail(
                    subject, 
                    message, 
                    'your_verified_email@example.com', 
                    [email],
                    fail_silently=False,
                )
            except Exception as email_error:
                # Log the email sending error
                logger.error(f"Email send error: {email_error}")
                # Delete the user if email fails
                signup_obj.delete()
                messages.error(request, "OTP could not be sent. Please contact support.")
                return redirect('signup')

            messages.success(request, "Account created successfully. OTP sent to your email.")
            # Use reverse for better URL resolution
            try:
                from django.urls import reverse
                redirect_url = reverse('userotp')
                logger.debug(f"Redirecting to: {redirect_url}")
                return redirect(redirect_url)
            
            except Exception as e:
                logger.error(f"URL resolution error: {e}")
                return redirect('userotp')


            except:
                # Fallback to regular redirect if reverse fails
                return redirect('userotp')

        except Exception as e:
            # Log the error
            logger.error(f"Signup error: {e}")
            messages.error(request, "An error occurred during signup. Please try again.")
            return redirect('signup')

    return render(request, 'authentication1/usersignup.html')



def userotp(request):
    # Debug session data
    logger.debug(f"OTP page accessed. Session contains: OTP: {request.session.get('otp')}, "
                f"Email: {request.session.get('email')}, User ID: {request.session.get('signup_user_id')}")
    
    # Check if necessary session data exists
    if not (request.session.get('otp') and request.session.get('email') and request.session.get('signup_user_id')):
        messages.error(request, "Session data is missing. Please sign up again.")
        return redirect('signup')
    
    if request.method == "POST":
        entered_otp = (
            request.POST.get('otp1', '') +
            request.POST.get('otp2', '') +
            request.POST.get('otp3', '') +
            request.POST.get('otp4', '')
        )
        
        stored_otp = request.session.get('otp')
        email = request.session.get('email')
        user_id = request.session.get('signup_user_id')
        
        logger.debug(f"OTP validation: Entered={entered_otp}, Stored={stored_otp}")
        
        if entered_otp == str(stored_otp):
            try:
                # Get and activate the user
                user = usertable.objects.get(id=user_id)
                user.is_active = True  # Activate the account
                user.save()
                
                # Clear session data
                request.session.pop('otp', None)
                request.session.pop('email', None)
                request.session.pop('signup_user_id', None)
                request.session.save()
                
                messages.success(request, "Account activated successfully. You can now log in.")
                return redirect('login')
            except usertable.DoesNotExist:
                messages.error(request, "User not found. Please sign up again.")
                return redirect('signup')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    # Pass email to the template for better user experience
    user_email = request.session.get('email', '')
    return render(request, 'authentication1/userotp.html', {'email': user_email})


def resend_otp(request):
    email = request.session.get('email')
    user_id = request.session.get('signup_user_id')

    if not email or not user_id:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect('signup')

    try:
        user = usertable.objects.get(id=user_id)
        new_otp = f"{random.randint(0, 9999):04d}"
        request.session['otp'] = new_otp
        print(f"Generated OTP for {email}: {new_otp}")
        # Send OTP via email
        subject = "Your New OTP for Verification"
        message = f"Hello,\n\nYour new OTP for account verification is: {new_otp}\n\nDo not share it with anyone."
        send_mail(subject, message, 'your_verified_email@example.com', [email])

        messages.success(request, "A new OTP has been sent to your email.")
        return redirect('userotp')
    except usertable.DoesNotExist:
        messages.error(request, "User not found. Please sign up again.")
        return redirect('signup')


def enteremail(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()

        # Check if the email exists in usertable
        users = usertable.objects.filter(email=email)

        if users.exists():
            user = users.first()  # Take the first user if multiple exist
        else:
            messages.error(request, "No account found with this email.")
            return redirect('resetemail')

        # Generate OTP
        otp = f"{random.randint(1000, 9999):04d}"
        print(otp)
        print(f"Generated OTP for {email}: {otp}")

        request.session['reset_otp'] = otp
        request.session['reset_email'] = email
        request.session['reset_user_id'] = user.id
        request.session.save()  # Explicitly save session

        print(f"Generated OTP for {email}: {otp}")
        # Send OTP via email
        subject = "Password Reset OTP"
        message = f"Hello,\n\nYour OTP for password reset is: {otp}\n\nDo not share it with anyone."
        send_mail(subject, message, 'your_email@gmail.com', [email])

        messages.success(request, "OTP sent to your email. Please verify.")

        # Redirect to OTP entry page
        return redirect('forgototp')

    return render(request, 'authentication1/resetpassword.html')

# ################################################################

def forgototp(request):
    if request.method == "POST":
        entered_otp = (
            request.POST.get('otp1', '') +
            request.POST.get('otp2', '') +
            request.POST.get('otp3', '') +
            request.POST.get('otp4', '')
        )
        
        stored_otp = request.session.get('reset_otp')  # Changed to reset_otp
        email = request.session.get('reset_email')     # Changed to reset_email

        # Debug print statements
        print(f"Entered OTP: {entered_otp}")
        print(f"Stored OTP: {stored_otp}")
        print(f"User Email: {email}")

        if not stored_otp:
            messages.error(request, "Session expired. Please enter your email again.")
            return redirect('resetemail')  

        if str(entered_otp) == str(stored_otp):
            messages.success(request, "OTP verified successfully. You can reset your password.")
            return redirect('resetpass') 
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'authentication1/forgototp.html')


def resendpassotp(request):
    email = request.session.get('reset_email')  # Changed to reset_email

    if not email:
        messages.error(request, "Session expired. Please enter your email again.")
        return redirect('resetemail')

    try:
        new_otp = f"{random.randint(0, 9999):04d}"
        request.session['reset_otp'] = new_otp  # Changed to reset_otp
        
        subject = "New Password Reset OTP"
        message = f"Hello,\n\nYour new OTP for password reset is: {new_otp}\n\nDo not share it with anyone."
        send_mail(subject, message, 'your_email@gmail.com', [email])

        messages.success(request, "A new OTP has been sent to your email.")
        return redirect('fogototp')
    except Exception as e:
        logger.error(f"Error resending password reset OTP: {e}")
        messages.error(request, "Failed to send OTP. Please try again.")
        return redirect('fogototp')

def resetpass(request):
    if request.method == "POST":
        new_password = request.POST.get('new-password')
        confirm_password = request.POST.get('confirm-password')

        # Get the email from the session
        email = request.session.get('email')

        if not email:
            messages.error(request, "Session expired. Please restart the password reset process.")
            return redirect('resetemail')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'authentication1/resetpass.html')

        
        if not validate_password_strength(new_password):
            messages.error(request, """Password must:
            - Be at least 8 characters long
            
            - Contain at least one lowercase letter
            - Contain at least one number
            - Contain at least one special character""")
            return render(request, 'authentication1/resetpass.html')

        try:
            user = usertable.objects.get(email=email)
            user.password = make_password(new_password)  # Hash the password before saving
            user.save()

            # Clear session data after password reset
            del request.session['email']
            del request.session['otp']

            messages.success(request, "Password reset successfully. You can now log in.")
            return redirect('login')

        except usertable.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('resetemail')

    return render(request, 'authentication1/resetpass.html')

@never_cache
def logoutPage(request):
    if request.user.is_authenticated:
        # Use email instead of username
        user_identifier = request.user.email
        logout(request)
        messages.info(request, f"Successfully logged out. Goodbye, {user_identifier}!")
        logger.info(f"Logout message added for user: {user_identifier}")
    return redirect('login')
