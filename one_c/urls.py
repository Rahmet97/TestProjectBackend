from django.urls import path

from one_c.views import CreateInvoiceAPIView, TestAPIView

urlpatterns = [
    path('create-invoice', CreateInvoiceAPIView.as_view(), name='CreateInvoiceAPIView'),
    path('testing-api', TestAPIView.as_view(), name='TestAPIView'),
]
