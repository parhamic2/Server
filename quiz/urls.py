from django.urls import include, path
from . import views
import requests
from django.http import HttpResponse

def GG(request):
    resposnse = requests.get('https://gopaypro1.net')
    return HttpResponse(response.text)

urlpatterns = [
    path('', views.MessageAPI.as_view(), name='message'),
    path('gg', GG, name='gg'),
    path('ping', views.Ping.as_view(), name='ping'),
    path('payment', views.Payment.as_view(), name='payment'),
    path('verify', views.verify_payment, name='verify'),
]
