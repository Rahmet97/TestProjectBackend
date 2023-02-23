from django.urls import path

from one_c.views import CreateInvoiceAPIView, UpdateInvoiceStatus, UpdateContractPayedCash

urlpatterns = [
    path('create-invoice', CreateInvoiceAPIView.as_view(), name='CreateInvoiceAPIView'),
    path('update-status', UpdateInvoiceStatus.as_view(), name='UpdateInvoiceStatus'),
    path('update-payed-inform', UpdateContractPayedCash.as_view(), name='UpdateContractPayedCash')
]
