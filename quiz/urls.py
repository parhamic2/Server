from django.urls import include, path
from . import views


urlpatterns = [
    path('', views.MessageAPI.as_view(), name='message'),
    path('ping', views.Ping.as_view(), name='ping'),
    path('telegram_forward', views.TelegramForward.as_view(), name='telegram_forward'),
    path('payment', views.Payment.as_view(), name='payment'),
    path('verify', views.verify_payment, name='verify'),
]
