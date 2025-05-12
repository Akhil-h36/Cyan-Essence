"""
URL configuration for cyan project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from adminapp import views as admin_views
from user import views as useraction_views
from authentication1 import views as authentication1
from userprofile import views as userprofile
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # path('admin/', admin.site.urls),
    path('adminapp/',include('adminapp.urls')),  # Admin app URLs
    path('user/', include('user.urls')),  # User app URLs  
    path('auth/', include('authentication1.urls')),
    path('userp/', include('userprofile.urls')),
    path('', include('user.urls')),
    path('accounts/', include('allauth.urls')),
] + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
