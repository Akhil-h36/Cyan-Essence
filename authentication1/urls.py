from django.urls import path
from .import views



urlpatterns=[  
     path('login/', views.userlogin, name='login'),
     path('signup/', views.usersignup, name='signup'),
     path('otppage/', views.userotp, name='userotp'),
     path('resendotp/', views.resend_otp, name='resendotp'),
     path('resetemail/',views.enteremail, name='resetemail'),
     path('resendpassotp/', views.resendpassotp, name='resendpassotp'),
     path('forgototp/',views.forgototp, name='fogototp'),
     path('resetpass/',views. resetpass, name='resetpass'), 
     path('logout/',views.logoutPage, name='logout'), 
]