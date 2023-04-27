from django.urls import path

from .views import TariffCreateAPIView, ColocationTariffSummAPIView, ElementAPIView

urlpatterns = [
    # path('tarif-create', TariffCreateAPIView.as_view(), name='TariffCreateAPIView'),
    path('calculate-colocation', ColocationTariffSummAPIView.as_view(), name='ColocationTariffSummAPIView'),
    path('element', ElementAPIView.as_view(), name='ElementAPIView'),
]
