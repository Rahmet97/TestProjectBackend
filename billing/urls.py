from django.urls import path

from .views import (
    ColocationTariffSummAPIView, ElementAPIView, InvoiceElementsAPIView, InvoiceElementsUpdateAPIView,
    ExpertiseTariffSummAPIView
)


urlpatterns = [
    # path('tarif-create', TariffCreateAPIView.as_view(), name='TariffCreateAPIView'),
    path('calculate-colocation', ColocationTariffSummAPIView.as_view(), name='ColocationTariffSummAPIView'),
    path('calculate-expertise', ExpertiseTariffSummAPIView.as_view(), name='ExpertiseTariffSummAPIView'),

    path('element', ElementAPIView.as_view(), name='ElementAPIView'),
    path('invoice-element', InvoiceElementsAPIView.as_view(), name='InvoiceElementsAPIView'),
    path('invoice-element-update/<int:pk>', InvoiceElementsUpdateAPIView.as_view(), name='InvoiceElementsUpdateAPIView'),
]
