import json
import os

import requests
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views import View
from dotenv import load_dotenv
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
load_dotenv()


class OneIDLoginView(View):
    def get(self, request):
        response_type = 'one_code'
        client_id = os.getenv("CLIENT_ID")
        redirect_uri = os.getenv("REDIRECT_URI")
        scope = os.getenv("SCOPE")
        state = os.getenv("STATE")
        base_url = os.getenv("BASE_URL")
        url = base_url + '?response_type=' + response_type + '&client_id=' + client_id + '&redirect_uri=' + redirect_uri + '&scope=' + scope + '&state=' + state
        return redirect(url)


class LoginView(View):
    def post(self, request):
        grant_type = 'one_authorization_code'
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv('CLIENT_SECRET')
        redirect_uri = os.getenv("REDIRECT_URL")
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


class GetUser(View):
    def post(self, request):
        grant_type = 'one_access_token_identify'
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv('CLIENT_SECRET')
        access_token = request.META.get("HTTP_AUTHENTICATION")
        scope = os.getenv("SCOPE")
        base_url = os.getenv("BASE_URL")
        res = requests.post(base_url, {"grant_type": grant_type, "client_id": client_id, "client_secret": client_secret, "access_token": access_token, "scope": scope})
        if res.status_code == 200:
            return JsonResponse(json.loads(res.content))
        else:
            return JsonResponse({"error": "Xatolik!"})
