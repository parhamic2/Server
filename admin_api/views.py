import random
import time

from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import View

from django.utils import timezone

from quiz.models import User
from rest_framework.permissions import AllowAny

class AdminAPI(APIView):
    permission_classes = [AllowAny]

    def user_detail(self, data):
        user = User.objects.get(username=data.get('username'))
        return Response({
            'coins': user.coins,
            'trophy': user.trophy,
            'copouns': user.copouns,
            'level_reached': user.level_reached,
            'date_joined': user.date_joined.strftime("%D %H:%m"),
            'phone': user.phone,
            'username': user.username,
            'xp': user.xp,
            'child_list': user.childs.all().values_list('username', flat=True),
            'read_fields': ['trophy', 'copouns', 'level_reached', 'date_joined', 'phone', 'username', 'xp'],
            'write_fields': ['coins']
        })

    def users_list(self, data):
        users = User.objects.exclude(username__startswith="GUEST#")
        return Response(
            {
                "headers": ["Name", "Coins", "XP", "Level", "Date", "Device"],
                "users": [
                    [
                        user.username,
                        user.coins,
                        user.xp,
                        user.level_reached,
                        user.date_joined.strftime("%D %H:%m"),
                        "iOS" if "-" in user.device_id else "Android",
                    ]
                    for user in users
                ],
            }
        )

    def post(self, request):
        method_type = request.data.get("type")
        return getattr(self, method_type)(request.data)
