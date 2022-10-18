from django.urls import path

from contracts.views import ListAllServicesAPIView, ListGroupServicesAPIView, ServiceDetailAPIView, \
    UserDetailAPIView, TarifListAPIView, DeviceListAPIView, OfferCreateAPIView, \
    OfferDetailAPIView, GetGroupAdminDataAPIView, ServiceCreateAPIView, DocumentCreateAPIView, SavedServiceAPIView, \
    SelectedTarifDevicesAPIView, TarifAPIView, DeleteSavedService, CreateContractFileAPIView

urlpatterns = [
    path('services', ListAllServicesAPIView.as_view(), name='ListAllServicesAPIView'),
    path('group-services', ListGroupServicesAPIView.as_view(), name='ListGroupServicesAPIView'),
    path('service-detail/<int:pk>', ServiceDetailAPIView.as_view(), name='ServiceDetailAPIView'),
    path('user-detail', UserDetailAPIView.as_view(), name='UserDetailAPIView'),
    path('tarifs', TarifListAPIView.as_view(), name='TarifListAPIView'),
    path('devices', DeviceListAPIView.as_view(), name='DeviceListAPIView'),
    path('offer-create', OfferCreateAPIView.as_view(), name='OfferCreateAPIView'),
    path('offer-detail', OfferDetailAPIView.as_view(), name='OfferDetailAPIView'),
    path('group-admin', GetGroupAdminDataAPIView.as_view(), name='GetGroupAdminDataAPIView'),
    path('service-create', ServiceCreateAPIView.as_view(), name='ServiceCreateAPIView'),
    path('document-create', DocumentCreateAPIView.as_view(), name='DocumentAPIView'),
    path('saved-service', SavedServiceAPIView.as_view(), name='SavedServiceAPIView'),
    path('selected-tarif-devices', SelectedTarifDevicesAPIView.as_view(), name='SelectedTarifDevicesAPIView'),
    path('tarif-elements-devices', TarifAPIView.as_view(), name='TarifAPIView'),
    path('delete-saved-service/<int:pk>', DeleteSavedService.as_view(), name='DeleteSavedService'),
    path('contract-create', CreateContractFileAPIView.as_view(), name='CreateContractFileAPIView')
]
