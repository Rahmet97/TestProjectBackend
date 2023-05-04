import os
import json
import requests
import base64
from datetime import datetime

from rest_framework import response, views, permissions, authentication, status
from dotenv import load_dotenv

from accounts.models import FizUser, YurUser
from main.utils import responseErrorMessage
from contracts.models import Contract, UserContractTarifDevice, UserDeviceCount, ContractStatus
from expertiseService.models import ExpertiseServiceContract
from one_c.models import Invoice, Status, Nomenclature, PayedInformation


load_dotenv()


class CreateInvoiceAPIView(views.APIView):
    permission_classes = ()

    def post(self, request):
        url = os.getenv('ONE_C_HOST') + 'hs/invoices/add'
        username = os.getenv('ONE_C_LOGIN')
        password = os.getenv('ONE_C_PASSWORD')
        # contract_id = int(request.data['contract_id'])
        contract_id_code = request.data['contract_id_code']

        if str(contract_id_code).lower().startswith("c", 0, 2):
            contract = Contract.objects.get(id_code=contract_id_code)
        elif str(contract_id_code).lower().startswith("e", 0, 2):
            contract = ExpertiseServiceContract.objects.get(id_code=contract_id_code)
        else:
            responseErrorMessage(message="Contract does not exist", status_code=status.HTTP_404_NOT_FOUND)
        
        invoice = Invoice.objects.create(
            customer=contract.client,
            number=f'{contract.id_code}/{str(datetime.now().month).zfill(2)}{datetime.now().year % 100}',
            # contract=contract,
            contract_code=contract_id_code,
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
        
        products = None
        if str(contract_id_code).upper().startswith("C", 0, 2):  # co-location

            user_contract_tarif_device = UserContractTarifDevice.objects.get(contract=contract)
            contract = Contract.objects.get(id_code=contract_id_code)
            if contract.tarif.name == 'Rack-1':
                quantity = user_contract_tarif_device.rack_count
            else:
                quantity = 0
                for element in UserDeviceCount.objects.filter(user=user_contract_tarif_device):
                    quantity += element.device_count * element.units_count
            
            products = [{
                "nomenclatureID": Nomenclature.objects.get(service=contract.service).nomenclature,
                "quantity": quantity,
                "Price": round(float(contract.tarif.price), 3),
                "amount": round(float(contract.contract_cash) / 1.12, 3),
                "amountVAT": round(float(contract.contract_cash) / 1.12 * 0.12, 3)
            }]

        elif str(contract_id_code).upper().startswith("E", 0, 2):  # expertise
            products = [{
                "nomenclatureID": Nomenclature.objects.get(service=contract.service).nomenclature,
                "quantity": contract.expertisetarifcontract_set.count(),
                "Price": round(float(contract.contract_cash), 3),
                "amount": round(float(contract.contract_cash) / 1.12, 3),
                "amountVAT": round(float(contract.contract_cash) / 1.12 * 0.12, 3)
            }]

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
            "invoiceNum": f'{contract.id_code}/{invoice.number}',
            "сontractID": contract.contract_number,
            "agreementdate": str(contract.contract_date).replace(' ', 'T').split('+')[0].split('.')[0],
            "fullnumber": contract.id_code,
            "products": products
        }
        print(data)
        rspns = requests.get(url, headers=headers, data=json.dumps(data))
        return response.Response(rspns.content)


class UpdateInvoiceStatus(views.APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            number = request.data['invoiceNum']
            status = int(request.data['invoiceStatus'])
            document_type = request.data['documentType']
            status_object = Status.objects.get(status_code=status)
            invoice = Invoice.objects.get(number=number)
            invoice.status = status_object
            invoice.document_type = document_type
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
            return response.Response({"OperationResult": data}, status=405)
        return response.Response({"OperationResult": data}, status=200)


class UpdateContractPayedCash(views.APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            id_code = request.data['contractID']
            contract_code = request.data.get('contractCode', None)
            invoice_number = request.data.get('invoiceNum', None)
            customer_tin = request.data['customerTIN']
            payed_cash = float(request.data['payedCash'])
            payed_time = request.data['payedDate']
            currency = request.data['currency']
            comment = request.data['comment']
            customer_payment_account = request.data.get('customerPaymentAccount', None)
            customer_mfo = request.data.get('customerMFO', None)
            company_payment_account = request.data.get('companyPaymentAccount', None)

            if str(id_code).lower().startswith("c", 0, 2):
                contract = Contract.objects.get(id_code=id_code)
            if str(id_code).lower().startswith("e", 0, 2):
                contract = ExpertiseServiceContract.objects.get(id_code=id_code)

            contract.payed_cash = payed_cash
            contract.contract_status = ContractStatus.objects.get(name='Aktiv')
            contract.save()

            payed_inform = PayedInformation.objects.create(
                invoice=Invoice.objects.get(number=invoice_number),
                # contract=contract,
                payed_cash=payed_cash,
                payed_time=payed_time,
                contract_code=contract_code,
                customer_tin=customer_tin,
                currency=currency,
                comment=comment,
                customer_payment_account=customer_payment_account,
                customer_mfo=customer_mfo,
                company_payment_account=company_payment_account
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
            return response.Response({"OperationResult": data}, status=405)
        return response.Response({"OperationResult": data}, status=200)
