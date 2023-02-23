from django.urls import path

from contracts.views import (
    DeleteUserContract, GetRackContractDetailWithNumber, GetUnitContractDetailWithNumber,
    ListAllServicesAPIView, ListGroupServicesAPIView, ServiceDetailAPIView,
    UserDetailAPIView, TarifListAPIView, DeviceListAPIView, OfferCreateAPIView,
    OfferDetailAPIView, GetGroupAdminDataAPIView, ServiceCreateAPIView, DocumentCreateAPIView, SavedServiceAPIView,
    SelectedTarifDevicesAPIView, TarifAPIView, DeleteSavedService, CreateContractFileAPIView, SavePkcs, GetContractFile,
    GetUserContracts, GetContractFileWithID, ContractDetail, GetGroupContract, ConfirmContract,
    ConnectMethodListAPIView, GetPinnedUserDataAPIView, AddOldContractsViews
)

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
    path('group-pinned-user', GetPinnedUserDataAPIView.as_view(), name='GetPinnedUserDataAPIView'),
    path('service-create', ServiceCreateAPIView.as_view(), name='ServiceCreateAPIView'),
    path('document-create', DocumentCreateAPIView.as_view(), name='DocumentAPIView'),
    path('saved-service', SavedServiceAPIView.as_view(), name='SavedServiceAPIView'),
    path('selected-tarif-devices', SelectedTarifDevicesAPIView.as_view(), name='SelectedTarifDevicesAPIView'),
    path('tarif-elements-devices', TarifAPIView.as_view(), name='TarifAPIView'),
    path('delete-saved-service/<int:pk>', DeleteSavedService.as_view(), name='DeleteSavedService'),
    path('contract-create', CreateContractFileAPIView.as_view(), name='CreateContractFileAPIView'),
    path('save-pkcs', SavePkcs.as_view(), name='SavePkcs'),
    path('contract', GetContractFile.as_view(), name='GetContractFile'),
    path('contract-file-by-id', GetContractFileWithID.as_view(), name='GetContractFileWithID'),
    path('contract-detail/<int:pk>', ContractDetail.as_view(), name='ContractDetail'),

    path('add-old-contract/<str:usertype>', AddOldContractsViews.as_view(), name="add-old-contract"),

    path('user-contracts', GetUserContracts.as_view(), name='GetUserContracts'),
    path('group-contracts', GetGroupContract.as_view(), name='GetGroupContract'),
    path('confirm-contract', ConfirmContract.as_view(), name='ConfirmContract'),
    path('get-connect-methods', ConnectMethodListAPIView.as_view(), name='ConnectMethodListAPIView'),
    path('delete-contract', DeleteUserContract.as_view(), name='DeleteUserContract'),
    path('rack-contract-with-number', GetRackContractDetailWithNumber.as_view(), name='GetRackContractDetailWithNumber'),
    path('unit-contract-with-number', GetUnitContractDetailWithNumber.as_view(), name='GetUnitContractDetailWithNumber'),
]
