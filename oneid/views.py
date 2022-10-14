import json
import os

import requests
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from dotenv import load_dotenv
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import UserData, FizUser, YurUser
from accounts.serializers import FizUserSerializer, YurUserSerializer

load_dotenv()


class OneIDLoginView(APIView):
    permission_classes = ()

    def get(self, request):
        response_type = 'one_code'
        client_id = os.getenv("CLIENT_ID")
        redirect_uri = os.getenv("REDIRECT_URI")
        scope = os.getenv("SCOPE")
        state = os.getenv("STATE")
        base_url = os.getenv("BASE_URL")
        url = base_url + '?response_type=' + response_type + '&client_id=' + client_id + '&redirect_uri=' + redirect_uri + '&scope=' + scope + '&state=' + state
        return redirect(url)


class LoginView(APIView):
    permission_classes = ()

    def post(self, request):
        grant_type = 'one_authorization_code'
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv('CLIENT_SECRET')
        redirect_uri = os.getenv("REDIRECT_URI")
        code = request.META.get('HTTP_X_AUTH')

        res = requests.post(os.getenv("BASE_URL"), {
            'grant_type': grant_type,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': code
        })

        print(json.loads(res.content))

        return JsonResponse(json.loads(res.content))


class GetUser(APIView):
    permission_classes = ()

    def post(self, request):
        grant_type = 'one_access_token_identify'
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv('CLIENT_SECRET')
        access_token = request.META.get("HTTP_X_AUTHENTICATION")
        scope = os.getenv("SCOPE")
        base_url = os.getenv("BASE_URL")
        res = requests.post(base_url, {"grant_type": grant_type, "client_id": client_id, "client_secret": client_secret,
                                       "access_token": access_token, "scope": scope})
        if res.status_code == 200:
            data = json.loads(res.content)
            username = data['pin']
            password = data['first_name'][0] + data['pin'] + data['first_name'][-1]

            # UserData table ga yangi kirgan userni ma'lumotlarini yozish

            if UserData.objects.filter(username=username).exists():
                user = UserData.objects.get(username=username)
            else:
                user = UserData.objects.create_user(username=username, password=password)
            print(data)

            data['userdata'] = user.id
            data['pport_issue_date'] = json.loads(res.content)['_pport_issue_date']
            data['pport_expr_date'] = json.loads(res.content)['_pport_expr_date']
            if data['legal_info']:
                # YurUser table ga yangi kirgan userni ma'lumotlarini yozish
                if not YurUser.objects.filter(userdata=user).exists():
                    userr = YurUserSerializer(data=data)
                    userr.is_valid(raise_exception=True)
                    userr.save()
            else:
                # FizUser table ga yangi kirgan userni ma'lumotlarini yozish
                if not FizUser.objects.filter(userdata=user).exists():
                    userr = FizUserSerializer(data=data)
                    userr.is_valid(raise_exception=True)
                    userr.save()
            url = 'http://api.unicon.uz/auth/token/'
            req_data = {
                'username': username,
                'password': password
            }
            response = requests.post(url, req_data)
            return JsonResponse(response.json())
        else:
            return JsonResponse({"error": "Xatolik!"})
