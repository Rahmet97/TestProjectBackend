from celery import shared_task
import requests
from datetime import datetime, timedelta
from django.db.models import Q

from billing.models import InvoiceElements

from contracts.models import Contract

from expertiseService.models import ExpertiseServiceContract


@shared_task
def send_periodic_request():
    try:
        url = 'http://django:8000/one-c/create-invoice'
        invoice_elements = InvoiceElements.objects.filter(Q(is_automate=True),
                                                          (Q(date__gte=datetime.now() - timedelta(seconds=30)),
                                                           Q(date__lte=datetime.now()))).values('service__name')
        print(invoice_elements)
        for invoice_element in invoice_elements:
            if 'Co-location' in invoice_element.values():
                colocation_contracts = Contract.objects.filter(Q(contract_status__name="To'lov kutilmoqda") | \
                                                               Q(contract_status__name="Aktiv"))
                for contract in colocation_contracts:
                    response = requests.post(url, data={'contract_id_code': contract.id_code})  # contract_id_code
                    print(response.json())
            if 'EKSPERTIZA' in invoice_element.values():
                expertise_contracts = ExpertiseServiceContract.objects.filter(Q(contract_status=3) | \
                                                               Q(contract_status=4))
                for contract in expertise_contracts:
                    response = requests.post(url, data={'contract_id_code': contract.id_code})  # contract_id_code
                    print(response.json())
    except Exception as e:
        return f'{e}'
    return 'Done' # response.text