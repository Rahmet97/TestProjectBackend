from celery import shared_task
import requests
from datetime import datetime, timedelta
from django.db.models import Q

from billing.models import InvoiceElements


@shared_task
def send_periodic_request():
    url = 'http://django:8000/one-c/create-invoice'
    invoice_elements = InvoiceElements.objects.filter(Q(is_automate=True),
                                                      (Q(date__gte=datetime.now() - timedelta(seconds=30)),
                                                       Q(date__lte=datetime.now()))).values('service')
    response = requests.post(url, data={})  # contract_id_code
    return response.text