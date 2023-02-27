from django.urls import path

from .views import TariffCreateAPIView, TariffElementAPIView

urlpatterns = [
    path('tarif-create', TariffCreateAPIView.as_view(), name='TariffCreateAPIView'),
    path('tarif-element', TariffElementAPIView.as_view(), name='TariffElementAPIView'),
]
