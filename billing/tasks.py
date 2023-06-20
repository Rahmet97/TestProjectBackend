import requests
from celery import shared_task
from datetime import datetime, timedelta
from django.db.models import Q

from billing.models import InvoiceElements

from contracts.models import Contract

from expertiseService.models import ExpertiseServiceContract

from celery.utils.log import get_task_logger

from contracts.models import ContractStatus

logger = get_task_logger(__name__)


@shared_task
def send_periodic_request():
    try:
        url = 'http://django:8000/one-c/create-invoice'

        # invoice_elements = InvoiceElements.objects.filter(
        #     Q(is_automate=True),
        #     Q(date__day=datetime.now().day),
        #     (
        #         Q(date__time__gte=datetime.now().time() - timedelta(seconds=30)),
        #         Q(date__time__lte=datetime.now().time())
        #     )
        # ).values('service__name')

        # Get the current date and time
        now = datetime.now()

        # Calculate the time 30 seconds ago
        time_30_seconds_ago = now - timedelta(seconds=30)

        # Build the query using the datetime objects
        query = Q(
            is_automate=True,
            date__day=now.day,
            date__time__gte=time_30_seconds_ago.time(),
            date__time__lte=now.time(),
        )

        # Use the query to filter the records
        invoice_elements = InvoiceElements.objects.filter(query).values('service__name')

        print(invoice_elements)
        for invoice_element in invoice_elements:
            if 'Co-location' in invoice_element.values():
                colocation_contracts = Contract.objects.filter(
                    Q(contract_status__name="To'lov kutilmoqda") |
                    Q(contract_status__name="Aktiv") |
                    Q(is_free=False)
                )
                for contract in colocation_contracts:
                    logger.info(f"contract >>>> {contract.id_code}")
                    logger.info(f"contract_cash before >>>> {contract.contract_cash}")
                    contract.payed_cash = 0
                    response = requests.post(url, data={'contract_id_code': contract.id_code})  # contract_id_code
                    contract.save()
                    logger.info(f"contract_cash after >>>> {contract.contract_cash}")
                    print(response.json())
            if 'EKSPERTIZA' in invoice_element.values():
                expertise_contracts = ExpertiseServiceContract.objects.filter(
                    Q(contract_status=3) | Q(contract_status=4)
                )
                for contract in expertise_contracts:
                    response = requests.post(url, data={'contract_id_code': contract.id_code})  # contract_id_code
                    print(response.json())
    except Exception as e:
        return f'{e}'
    return 'Done'  # response.text


@shared_task
def contract_end():
    now = datetime.now()
    time_30_seconds_ago = now - timedelta(seconds=30)

    query = Q(
        expiration_date__gte=time_30_seconds_ago,
        expiration_date__lte=now.time(),
    )
    contracts = Contract.objects.filter(query)
    for contract in contracts:
        contract.contract_status = ContractStatus.objects.get(name='Yakunlangan')
        contract.save()
    return "Done"