from django.urls import path

from .views import (
    ColocationTariffSummAPIView, ElementAPIView, InvoiceElementsAPIView, InvoiceElementsUpdateAPIView,
    ExpertiseTariffSummAPIView, ElementUpdateAPIView, GetElementAPIView, VpsTariffSummAPIView
)


urlpatterns = [
    # path('tarif-create', TariffCreateAPIView.as_view(), name='TariffCreateAPIView'),
    path('calculate-colocation', ColocationTariffSummAPIView.as_view(), name='ColocationTariffSummAPIView'),
    path('calculate-expertise', ExpertiseTariffSummAPIView.as_view(), name='ExpertiseTariffSummAPIView'),
    path('calculate-vps', VpsTariffSummAPIView.as_view(), name='VpsTariffSummAPIView'),

    path('element', ElementAPIView.as_view(), name='ElementAPIView'),
    path('get-element', GetElementAPIView.as_view(), name='GetElementAPIView'),
    path('element-update-delete/<int:pk>', ElementUpdateAPIView.as_view(), name='ElementUpdateAPIView'),
    path('invoice-element', InvoiceElementsAPIView.as_view(), name='InvoiceElementsAPIView'),
    path('invoice-element-update/<int:pk>', InvoiceElementsUpdateAPIView.as_view(), name='InvoiceElementsUpdateAPIView'),
]
