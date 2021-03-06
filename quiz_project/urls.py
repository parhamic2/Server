from django.urls import include, path, re_path
from django.contrib import admin
from rest_framework import routers
from rest_framework.authtoken.views import ObtainAuthToken
from quiz import urls as quiz_urls
from admin_api import urls as admin_api_urls
from quiz.views import register_view, CustomLoginView

router = routers.DefaultRouter()

import requests
from django.http import HttpResponse

urlpatterns = [
    # re_path(r'^', GG, name='gg'),
    path('message/', include(quiz_urls)),
    path('admin_api/', include(admin_api_urls)),
    path('login', CustomLoginView.as_view(), name='obtain_auth_token'),
    path('register', register_view, name='register'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]
