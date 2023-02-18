from django.shortcuts import render
from rest_framework.views import APIView


class CreateInvoiceAPIView(APIView):
    permission_classes = ()

    def post(self, request):
        pass
