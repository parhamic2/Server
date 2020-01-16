import random
import time

from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import View

from django.utils import timezone

from quiz.models import User


class AdminAPI(APIView):
    permission_classes = []

    def users_list(self, data):
        users = User.objects.all()
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
