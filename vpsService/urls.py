from django.urls import path

from . import views

# # Define the URL patterns
urlpatterns = [
    # URL pattern for the list of operation systems
    path('operations-systems-list/', views.OperationSystemListView.as_view(), name="operations-systems-list"),

    path('tariff-list/', views.VpsTariffListView.as_view(), name="tariff-list"),

    # URL pattern for the list of operation system versions with a dynamic operation_system_id parameter
    path(
        'operations-systems-version-list/<str:operation_system_id>',
        views.OperationSystemVersionListView.as_view(),
        name="operations-systems-version-list"
    ),

    path(
        'contract-create',
        views.CreateVpsServiceContractViaClientView.as_view(),
        name='CreateVpsServiceContractViaClientView'
    ),

    # Endpoint to confirm an expertise service contract
    path(
        'confirm-contract',
        views.VpsConfirmContract.as_view(),
        name='VpsConfirmContract'
    ),

    # Endpoint to get the contract file by its hash code
    path('contract/<str:hash_code>', views.VpsGetContractFile.as_view(), name='VpsGetContractFile'),

    # Endpoint to get all expertise service contracts that the authenticated user is a participant in
    path('user-contracts', views.VpsGetUserContractsViews.as_view(), name='VpsGetUserContractsViews'),

    # Endpoint to get details of an expertise service contract by its primary key
    path('contract-detail/<int:pk>', views.VpsContractDetail.as_view(), name='VpsContractDetail'),

    # Endpoint to get all expertise service contracts for a particular group
    path('group-contracts', views.VpsGetGroupContract.as_view(), name='VpsGetGroupContract'),

    path('reject/<int:pk>', views.DeleteVpsContractView.as_view(),name='DeleteVpsContractView'),

    path('file', views.FileUploadAPIView.as_view(), name='file_upload'),
    path('new-file', views.NewFileCreateAPIView.as_view(), name='newfile_upload'),
    path('convert-to-pdf/', views.ConvertDocx2PDFAPIView.as_view(), name='convert_to_pdf'),
    path('save-file/', views.ForceSaveFileAPIView.as_view(), name='save_file'),
    path('callback-url/', views.CallbackUrlAPIView.as_view(), name='callback_url'),

    path('save-pkcs', views.VpsSavePkcs.as_view(), name='VpsSavePkcs'),
]
