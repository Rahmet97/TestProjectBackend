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
        views.OperationSystemVersionListView.as_view(), name="operations-systems-version-list"
    ),

    path(
        'contract-create', views.CreateVpsServiceContractViaClientView.as_view(),
        name='CreateVpsServiceContractViaClientView'
    ),

    # path('reject/<int:pk>', views.VpsServiceContractDeleteAPIView.as_view(), name='VpsServiceContractDeleteAPIView'),

    path('file', views.FileUploadAPIView.as_view(), name='file_upload'),
    path('new-file', views.NewFileCreateAPIView.as_view(), name='newfile_upload'),
    path('convert-to-pdf/', views.convert_to_pdf, name='convert_to_pdf'),

]
