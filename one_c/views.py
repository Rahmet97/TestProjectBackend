import os
import json
import requests
import base64
from datetime import datetime

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication
from dotenv import load_dotenv

from accounts.models import FizUser, YurUser
from contracts.models import Contract, UserContractTarifDevice, UserDeviceCount, ContractStatus
from one_c.models import Invoice, Status, Nomenclature, PayedInformation

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
            number=f'{contract.id_code}/{str(datetime.now().month).zfill(2)}{datetime.now().year % 100}',
            contract=contract,
            status=Status.objects.get(name='Yangi')
        )
        invoice.save()
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}"
        }
        if invoice.customer.type == 1:
            user = FizUser.objects.get(userdata=invoice.customer)
            customer_name = user.full_name
            customer_inn = user.pin
            customer_nds = None
            customer_address = user.per_adr
            customer_account = None
            customer_mfo = None
        else:
            user = YurUser.objects.get(userdata=invoice.customer)
            customer_name = user.name
            customer_inn = user.tin
            customer_nds = None
            customer_address = user.per_adr
            customer_account = user.paymentAccount
            customer_mfo = user.bank_mfo.mfo
        user_contract_tarif_device = UserContractTarifDevice.objects.get(contract=contract)
        if invoice.contract.tarif.name == 'Rack-1':
            quantity = user_contract_tarif_device.rack_count
        else:
            quantity = 0
            for element in UserDeviceCount.objects.filter(user=user_contract_tarif_device):
                quantity += element.device_count * element.units_count
        data = {
            "ID": str(invoice.id),
            "customerID": str(invoice.customer.id),
            "customerName": customer_name,
            "customerINN": customer_inn,
            "customerNDS": customer_nds,
            "customerAdress": customer_address,
            "customerAccount": customer_account,
            "customerMFO": customer_mfo,
            "invoiceDate": str(invoice.date).replace(' ', 'T').split('.')[0],
            "invoiceNum": f'{invoice.contract.id_code}/{invoice.number}',
            "сontractID": invoice.contract.contract_number,
            "agreementdate": str(invoice.contract.contract_date).replace(' ', 'T').split('+')[0],
            "fullnumber": invoice.contract.id_code,
            "products": [{
                "nomenclatureID": Nomenclature.objects.get(service=invoice.contract.service).nomenclature,
                "quantity": quantity,
                "Price": float(invoice.contract.tarif.price),
                "amount": float(invoice.contract.contract_cash) / 1.12,
                "amountVAT": float(invoice.contract.contract_cash) / 1.12 * 0.12
            }]
        }
        print(data)
        print(json.dumps(data))
        response = requests.get(url, headers=headers, data=json.dumps(data))
        return Response(response.content)


class UpdateInvoiceStatus(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            number = request.data['invoiceNum']
            status = int(request.data['invoiceStatus'])
            status_object = Status.objects.get(status_code=status)
            invoice = Invoice.objects.get(number=number)
            invoice.status = status_object
            invoice.save()
            data = {
                "result": 0,
                "errorMessage": ""
            }
        except Exception as e:
            data = {
                "result": 1,
                "errorMessage": f"{e}"
            }
            return Response({"OperationResult": data}, status=405)
        return Response({"OperationResult": data}, status=200)


class UpdateContractPayedCash(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            id_code = request.data['contractID']
            invoice_number = request.data['invoiceNum']
            payed_cash = float(request.data['payedCash'])
            payed_time = request.data['payedDate']

            contract = Contract.objects.get(id_code=id_code)
            contract.payed_cash = payed_cash
            contract.contract_status = ContractStatus.objects.get(name='Aktiv')
            contract.save()

            payed_inform = PayedInformation.objects.create(
                invoice=Invoice.objects.get(number=invoice_number),
                contract=contract,
                payed_cash=payed_cash,
                payed_time=payed_time
            )
            payed_inform.save()
            data = {
                "result": 0,
                "errorMessage": ""
            }
        except Exception as e:
            data = {
                "result": 1,
                "errorMessage": f"{e}"
            }
            return Response({"OperationResult": data}, status=405)
        return Response({"OperationResult": data}, status=200)
