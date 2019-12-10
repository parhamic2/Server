import random
import time

from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import View

from .message_handlers import get_handlers, get_country
from .models import User, ShopItem, PlayRecord
from .serializers import MessageSerializer
from .utils import get_time
from .tasks import alive_message
from django.utils import timezone
from rest_framework.authtoken.views import ObtainAuthToken


def generate_password(length=16):
    pw = ""
    chrs = [chr(ch) for ch in range(ord('A'), ord('Z')+1)]
    chrs.extend([chr(ch) for ch in range(ord('0'), ord('9')+1)])
    for i in range(length):
        pw += random.choice(chrs)
    return pw


def register_view(request):
    # if request.method != 'POST':
    #     return Response('')
    username = "GUEST#{}".format(User.objects.count())
    password = generate_password()
    user = User.objects.create_user(username, None, password)
    token, created = Token.objects.get_or_create(user=user)
    return JsonResponse(
        {
            "token": token.key,
            "username": username,
            "password": password,
            "country": get_country(request),
        }
    )


class CustomLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "country": get_country(request)})


class MessageAPI(APIView):
    def get(self, request, format=None):
        print(request.user.username + " is online", flush=True)
        queryset = request.user.messages.filter(hidden=False)
        serializer = MessageSerializer(queryset, many=True)
        data = serializer.data  # save the data before deleting the queryset
        
        user = request.user
        record = PlayRecord.objects.filter(date__gte=get_time() - timezone.timedelta(hours=16), player=user)
        if record.count() == 0:
            record = PlayRecord.objects.create(player=user)
        else:
            record = record.first()
        
        if user.last_alive_message is not None:
            diff = (get_time() - user.last_alive_message)
            diff = diff.seconds * 10**6 + diff.microseconds
            diff = diff / (10**6)
            print ('Alive message Diff IS : {}'.format(diff))
            if diff < 5:
                record.played_time += diff
                record.played_time = int(record.played_time * 10) / 10
                record.save(update_fields=['played_time'])
        user.last_alive_message = get_time()
        user.save(update_fields=["last_alive_message"])

        alive_message.delay(
            request.user.pk, list(queryset.values_list("id", flat=True))
        )
        request.user.messages.filter(perminent=True).update(hidden=True)
        return Response(data)

    def post(self, request, format=None):
        cmd = request.data["cmd"]
        if cmd not in get_handlers():
            return Response('{"cmd":"COMMAND_NOT_FOUND"}')
        handler = get_handlers()[cmd](request)
        return handler.handle()


class Ping(APIView):
    def get(self, request):
        return Response("done")


from zeep import Client
from django.shortcuts import redirect
from django.http import HttpResponse
from zeep import Client
from .models import ZarinPayment
from rest_framework.authtoken.models import Token

MERCHANT = 'be30cfac-cbbf-11e9-933e-000c295eb8fc'

class Payment(View):
    def get(self, request):
        client = Client('https://www.zarinpal.com/pg/services/WebGate/wsdl')

        item = request.GET.get('item', '')
        amount = ShopItem.objects.get(pk=item).price
        description = "جان جیبی"  # Required
        email = 'kh.gh.game@gmail.com'  # Optional
        mobile = '09123456789'  # Optional
        CallbackURL = 'http://46.45.163.65:81/message/verify'
        result = client.service.PaymentRequest(MERCHANT, amount, description, email, mobile, CallbackURL)
        if result.Status == 100:
            authority = str(int(str(result.Authority)))
            ZarinPayment.objects.create(authority=authority, amount=amount, 
                    user=Token.objects.get(key=request.GET.get('token', '')).user, item=item)
            return redirect('https://www.zarinpal.com/pg/StartPay/' + authority)
        else:
            return HttpResponse('Error code: ' + str(result.Status))

def verify_payment(request):
    if request.GET.get('Status') == 'OK':
        client = Client('https://www.zarinpal.com/pg/services/WebGate/wsdl')
        authority = str(int(str(request.GET['Authority'])))
        payment = ZarinPayment.objects.get(authority=authority)
        if payment.is_done:
            return
        result = client.service.PaymentVerification(MERCHANT, request.GET['Authority'], payment.amount)
        if result.Status == 100:
            payment.is_done = True
            shop_item = ShopItem.objects.get(pk=payment.item)
            payment.user.spent += shop_item.price
            payment.user.coins += shop_item.coins
            payment.user.save()
            payment.save()
            return HttpResponse('Transaction success.\nRefID: ' + str(result.RefID))
        elif result.Status == 101:
            return HttpResponse('Transaction submitted : ' + str(result.Status))
        else:
            return HttpResponse('Transaction failed.\nStatus: ' + str(result.Status))
    else:
        return HttpResponse('Transaction failed or canceled by user')