import os
import json
import requests
import base64
from datetime import datetime

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from dotenv import load_dotenv

from accounts.models import FizUser, YurUser
from contracts.models import Contract, UserContractTarifDevice, UserDeviceCount
from one_c.models import Invoice, Status, Nomenclature

load_dotenv()


class CreateInvoiceAPIView(APIView):
    permission_classes = ()

    def post(self, request):
        url = os.getenv('ONE_C_HOST') + 'hs/invoices/add'
        username = os.getenv('ONE_C_LOGIN')
        password = os.getenv('ONE_C_PASSWORD')
        contract_id = int(request.data['contract_id'])
        contract = Contract.objects.get(pk=contract_id)
        invoice = Invoice.objects.create(
            customer=contract.client,
            number=f'{datetime.now().month}{datetime.now().year % 100}',
            contract=contract,
            status=Status.objects.get(name='Yangi')
        )
        invoice.save()
        headers = {
            'Authorization': f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"
        }
        if invoice.customer.type == 1:
            customer_name = FizUser.objects.get(userdata=invoice.customer).full_name
        else:
            customer_name = YurUser.objects.get(userdata=invoice.customer).name
        user_contract_tarif_device = UserContractTarifDevice.objects.get(contract=contract)
        if invoice.contract.tarif.name == 'Rack-1':
            quantity = user_contract_tarif_device.rack_count
        else:
            quantity = 0
            for element in UserDeviceCount.objects.filter(user=user_contract_tarif_device):
                quantity += element.device_count * element.units_count
        data = {
            'ID': str(invoice.id),
            'customerID': invoice.customer.id,
            'customerName': customer_name,
            'invoiceDate': invoice.date,
            'invoiceNum': f'{invoice.contract.id_code}/{invoice.number}',
            'agreementdate': invoice.contract.contract_date,
            'fullnumber': invoice.contract.id_code,
            'contractID': invoice.contract.contract_number,
            'products': [{
                'nomenclatureID': Nomenclature.objects.get(service=invoice.contract.service).nomenclature,
                'quantity': quantity,
                'Price': float(invoice.contract.tarif.price),
                'amount': float(invoice.contract.contract_cash),
                'amountVAT': float(invoice.contract.contract_cash) * 0.12
            }]
        }
        print(data)
        response = requests.get(url, headers=headers, data=data)
        print(response)
        print(response.content)
        return Response(response)
