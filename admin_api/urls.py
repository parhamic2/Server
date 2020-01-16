from django.urls import include, path
from . import views


urlpatterns = [
    path('', views.AdminAPI.as_view(), name='admin_api'),
]
