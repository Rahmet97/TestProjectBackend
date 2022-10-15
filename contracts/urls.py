from django.urls import path

from contracts.views import ListAllServicesAPIView, ListGroupServicesAPIView, ServiceDetailAPIView, \
    FizUserDetailAPIView, TarifListAPIView, DeviceListAPIView, UserContractTarifDeviceCreateAPIView, OfferCreateAPIView, \
    OfferDetailAPIView, GetGroupAdminDataAPIView, ServiceCreateAPIView, DocumentCreateAPIView

urlpatterns = [
    path('services', ListAllServicesAPIView.as_view(), name='ListAllServicesAPIView'),
    path('group-services', ListGroupServicesAPIView.as_view(), name='ListGroupServicesAPIView'),
    path('service-detail/<int:pk>', ServiceDetailAPIView.as_view(), name='ServiceDetailAPIView'),
    path('fizuser-detail', FizUserDetailAPIView.as_view(), name='FizUserDetailAPIView'),
    path('tarifs', TarifListAPIView.as_view(), name='TarifListAPIView'),
    path('devices', DeviceListAPIView.as_view(), name='DeviceListAPIView'),
    path('user-contract-tarif-device-create', UserContractTarifDeviceCreateAPIView.as_view(), name='UserContractTarifDeviceCreateAPIView'),
    path('offer-create', OfferCreateAPIView.as_view(), name='OfferCreateAPIView'),
    path('offer-detail/<int:pk>', OfferDetailAPIView.as_view(), name='OfferDetailAPIView'),
    path('group-admin', GetGroupAdminDataAPIView.as_view(), name='GetGroupAdminDataAPIView'),
    path('service-create', ServiceCreateAPIView.as_view(), name='ServiceCreateAPIView'),
    path('document-create', DocumentCreateAPIView.as_view(), name='DocumentAPIView'),
]
