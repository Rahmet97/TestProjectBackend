import json
import os

import requests
from django.http import JsonResponse
from django.shortcuts import redirect
from dotenv import load_dotenv
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt import tokens
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserData, FizUser, YurUser, Role
from accounts.serializers import FizUserSerializer, YurUserSerializer

load_dotenv()


class OneIDLoginView(APIView):
    permission_classes = ()

    def get(self, request):
        response_type = 'one_code'
        client_id = os.getenv("CLIENT_ID")
        redirect_uri = request.GET.get('path') + '/code'
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
        redirect_uri = request.META.get('HTTP_X_PATH') + '/code'
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

    def kiril2latin(self, text):
        host = os.getenv("MATN_UZ_HOST")
        token = os.getenv("MATN_UZ_TOKEN")
        url = host + '/latin'
        response = requests.post(url, headers={'Authorization': 'Bearer ' + token}, data={'text': text})

        return response.json()

    def post(self, request):
        grant_type = 'one_access_token_identify'
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv('CLIENT_SECRET')
        access_token = request.META.get("HTTP_X_AUTHENTICATION")
        is_client = request.data["is_client"]
        scope = os.getenv("SCOPE")
        base_url = os.getenv("BASE_URL")
        res = requests.post(base_url, {"grant_type": grant_type, "client_id": client_id, "client_secret": client_secret,
                                       "access_token": access_token, "scope": scope})
        if res.status_code == 200:
            data = json.loads(res.content)
            if data['legal_info']:
                username = data['legal_info'][0]['tin']
                password = data['first_name'][0] + data['legal_info'][0]['tin'] + data['first_name'][-1]
            else:
                username = data['pin']
                password = data['first_name'][0] + data['pin'] + data['first_name'][-1]

            # UserData table ga yangi kirgan userni ma'lumotlarini yozish

            if UserData.objects.filter(username=username).exists():
                user = UserData.objects.get(username=username)
            else:
                if int(is_client):
                    client_role = Role.objects.get(name='mijoz')
                else:
                    client_role = None
                if data['legal_info']:
                    user = UserData.objects.create_user(username=username, password=password, type=2, role=client_role)
                else:
                    user = UserData.objects.create_user(username=username, password=password, type=1, role=client_role)
            print(data)

            data['userdata'] = user.id
            data['pport_issue_date'] = json.loads(res.content)['_pport_issue_date']
            data['pport_expr_date'] = json.loads(res.content)['_pport_expr_date']
            data['ctzn'] = self.kiril2latin(data['ctzn'])
            data['per_adr'] = self.kiril2latin(data['per_adr'])
            data['pport_issue_place'] = self.kiril2latin(data['pport_issue_place'])
            data['natn'] = self.kiril2latin(data['natn'])
            if data['legal_info']:
                # YurUser table ga yangi kirgan userni ma'lumotlarini yozish
                data['name'] = data['legal_info'][0]['acron_UZ']
                data['tin'] = data['legal_info'][0]['tin']
                if not YurUser.objects.filter(userdata=user).exists():
                    userr = YurUserSerializer(data=data)
                    userr.is_valid(raise_exception=True)
                    userr.save()
                else:
                    pass
            else:
                # FizUser table ga yangi kirgan userni ma'lumotlarini yozish
                if not FizUser.objects.filter(userdata=user).exists():
                    userr = FizUserSerializer(data=data)
                    userr.is_valid(raise_exception=True)
                    userr.save()
                else:
                    pass
            token = tokens.RefreshToken.for_user(user)
            tk = {
                "access": str(token.access_token),
                "refresh": str(token),
            }
            return JsonResponse(tk)
        else:
            return JsonResponse({"error": "Xatolik!"})


class Logout(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        grant_type = 'one_log_out'
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv('CLIENT_SECRET')
        access_token = request.META.get("HTTP_X_AUTHENTICATION")
        scope = os.getenv("SCOPE")
        base_url = os.getenv("BASE_URL")
        refresh_token = request.data["refresh_token"]

        requests.post(base_url, {
            'grant_type': grant_type,
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': access_token,
            'scope': scope
        })

        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response(status=205)
