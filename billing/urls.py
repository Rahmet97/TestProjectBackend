from django.urls import path

from .views import TariffCreateAPIView, CalculateTariffSummAPIView, ElementAPIView

urlpatterns = [
    path('tarif-create', TariffCreateAPIView.as_view(), name='TariffCreateAPIView'),
    path('calculate', CalculateTariffSummAPIView.as_view(), name='CalculateTariffSummAPIView'),
    path('element', ElementAPIView.as_view(), name='ElementAPIView'),
]
