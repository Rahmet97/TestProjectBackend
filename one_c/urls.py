from django.urls import path

from one_c.views import CreateInvoiceAPIView

urlpatterns = [
    path('create-invoice', CreateInvoiceAPIView.as_view(), name='CreateInvoiceAPIView')
]
