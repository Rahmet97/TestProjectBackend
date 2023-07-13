import logging
import os
import json
import requests
import base64
from datetime import datetime
from django.db.models import Q

from rest_framework import response, views, permissions, authentication, status, generics, serializers
from dotenv import load_dotenv

from accounts.models import FizUser, YurUser
from main.utils import responseErrorMessage
from contracts.models import Contract, UserContractTarifDevice, UserDeviceCount, ContractStatus
from expertiseService.models import ExpertiseServiceContract
from vpsService.models import VpsServiceContract
from one_c.models import Invoice, Status, Nomenclature, PayedInformation

logger = logging.getLogger(__name__)

load_dotenv()


class CreateInvoiceAPIView(views.APIView):
    permission_classes = ()

    def get_contract_by_id_code(self, contract_id_code):

        if str(contract_id_code).lower().startswith("c", 0, 2):
            contract = Contract.objects.get(id_code=contract_id_code, is_free=False)
        elif str(contract_id_code).lower().startswith("e", 0, 2):
            contract = ExpertiseServiceContract.objects.get(id_code=contract_id_code)
        elif str(contract_id_code).lower().startswith("vm", 0, 2):
            contract = VpsServiceContract.objects.get(id_code=contract_id_code)
        else:
            return response.Response(data={"error": "Contract does not exist"}, status=status.HTTP_404_NOT_FOUND)

        return contract

    # def get_month_and_year(self, month=None, year=None):
    #     """month -> m; year -> y"""
    #     if month and year:
    #         m, y = int(month), int(year)
    #     else:
    #         m, y = datetime.now().month, datetime.now().year
    #     return m, y

    def get_month_and_year(self, month=None, year=None):
        """month -> m; year -> y"""
        now = datetime.now()
        m = int(month) if month else now.month
        y = int(year) if year else now.year
        return m, y

    def get_invoice_count(self, contract, month, year):
        return Invoice.objects.filter(
            number__startswith=f'{contract.id_code}/{str(month).zfill(2)}{year % 100}'
        ).count()

    def create_invoice(self, contract, comment, inv_count, contract_id_code, m, y):
        invoice = Invoice.objects.create(
            customer=contract.client,
            number=f'{contract.id_code}/{str(m).zfill(2)}{y % 100}/{inv_count + 1}',
            comment=comment,
            contract_code=contract_id_code,
            status=Status.objects.get(name='Yangi')
        )
        invoice.save()
        return invoice

    def get_products(self, contract_id_code, contract):
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

        elif str(contract_id_code).upper().startswith("VM", 0, 2):  # vps
            products = [{
                "nomenclatureID": Nomenclature.objects.get(service=contract.service).nomenclature,
                "quantity": contract.vps_contract_device.count(),
                "Price": round(float(contract.contract_cash), 3),
                "amount": round(float(contract.contract_cash) / 1.12, 3),
                "amountVAT": round(float(contract.contract_cash) / 1.12 * 0.12, 3)
            }]

        return products

    def post(self, request):
        url = os.getenv('ONE_C_HOST') + 'hs/invoices/add'
        username = os.getenv('ONE_C_LOGIN')
        password = os.getenv('ONE_C_PASSWORD')
        # contract_id = int(request.data['contract_id'])
        contract_id_code = request.data['contract_id_code']
        month = request.data.get('month', None)
        year = request.data.get('year', None)
        comment = request.data['comment']

        contract = self.get_contract_by_id_code(contract_id_code)
        m, y = self.get_month_and_year(month, year)
        inv_count = self.get_invoice_count(contract, m, y)
        invoice = self.create_invoice(contract, comment, inv_count, contract_id_code, m, y)

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

        products = self.get_products(contract_id_code, contract)

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
            "invoiceNum": f'{invoice.number}',
            "comment": comment,
            "contractID": contract.contract_number,
            "agreementdate": str(contract.contract_date).replace(' ', 'T').split('+')[0].split('.')[0],
            "fullnumber": contract.id_code,
            "products": products
        }
        logger.info(data)
        res = requests.get(url, headers=headers, data=json.dumps(data))
        logger.info(f"res.content >> {res.content}")
        logger.info(f"res.status_code >> {res.status_code}")
        return response.Response(res.content)


class UpdateInvoiceStatus(views.APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            number = request.data['invoiceNum']
            invoice_id = request.data['invoiceID']
            status = int(request.data['invoiceStatus'])
            document_type = request.data['documentType']
            status_object = Status.objects.get(status_code=status)
            invoice = Invoice.objects.get(pk=invoice_id)
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
            print(request.data)

            id_code = request.data['contractID']
            contract_code = request.data.get('contractCode', None)
            invoice_id = request.data.get('invoiceID', None)
            invoice_number = request.data.get('invoiceNum', None)
            customer_tin = request.data['customerTIN']
            payed_cash = float(request.data['payedCash'])
            payed_time = request.data['payedDate']
            currency = request.data['currency']
            comment = request.data['comment']
            customer_payment_account = request.data.get('customerPaymentAccount', None)
            customer_mfo = request.data.get('customerMFO', None)
            company_payment_account = request.data.get('companyPaymentAccount', None)

            print('id_code >>>>> ', id_code)
            print('contract_code >>>>> ', contract_code)
            print('invoice_id >>>>> ', invoice_id)
            print('invoice_number >>>>> ', invoice_number)
            print('customer_tin >>>>> ', customer_tin)
            print('payed_cash >>>>> ', payed_cash)
            print('payed_time >>>>> ', payed_time)
            print('currency >>>>> ', currency)
            print('comment >>>>> ', comment)
            print('customer_payment_account >>>>> ', customer_payment_account)
            print('customer_mfo >>>>> ', customer_mfo)
            print('company_payment_account >>>>> ', company_payment_account)
            contract = None
            contract_status = None

            if str(contract_code).lower().startswith("c", 0, 2):
                contract = Contract.objects.get(id_code=contract_code, is_free=False)
                contract_status = ContractStatus.objects.get(name='Aktiv')
            if str(contract_code).lower().startswith("e", 0, 2):
                contract = ExpertiseServiceContract.objects.get(id_code=contract_code)
                contract_status = 4  # ACTIVE
            if str(contract_code).upper().startswith("VM", 0, 2):  # vps
                contract = VpsServiceContract.objects.get(id_code=contract_code)
                contract_status = 3  # ACTIVE
            contract.payed_cash = payed_cash
            contract.contract_status = contract_status
            contract.save()

            if not invoice_number:
                invoice_number = Invoice.objects.filter(
                    Q(number__startswith=contract_code) | Q(status__name='Yangi')
                ).order_by('id').last().number

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


# Test api
class InvoiceSerializers(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"


class ListInvoiceAPIView(generics.ListAPIView):
    serializer_class = InvoiceSerializers
    queryset = Invoice.objects.all()
