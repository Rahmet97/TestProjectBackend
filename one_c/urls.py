from django.urls import path

from one_c.views import CreateInvoiceAPIView, UpdateInvoiceStatus

urlpatterns = [
    path('create-invoice', CreateInvoiceAPIView.as_view(), name='CreateInvoiceAPIView'),
    path('update-status', UpdateInvoiceStatus.as_view(), name='UpdateInvoiceStatus'),
]
