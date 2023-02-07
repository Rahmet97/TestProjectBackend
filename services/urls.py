from django.urls import path
from .views import GetRackInfo, RackAPIView, RackDetailAPIView, UpdateRackAPIView, DevicePublisherAPIView, \
    AddDeviceAPIView, DeviceUnitDetail, DeleteDeviceAPIView, ListInternetProviderAPIView

urlpatterns = [
    path('rack', RackAPIView.as_view(), name='RackAPIView'),
    path('update-rack/<int:pk>', UpdateRackAPIView.as_view(), name='UpdateRackAPIView'),
    path('get-info', GetRackInfo.as_view(), name='GetRackInfo'),
    path('rack-detail', RackDetailAPIView.as_view(), name='RackDetailAPIView'),
    path('list-publisher', DevicePublisherAPIView.as_view(), name='DevicePublisherAPIView'),
    path('add-device', AddDeviceAPIView.as_view(), name='AddDeviceAPIView'),
    path('device-detail', DeviceUnitDetail.as_view(), name='DeviceUnitDetail'),
    path('delete-device', DeleteDeviceAPIView.as_view(), name='DeleteDeviceAPIView'),
    path('list-provider', ListInternetProviderAPIView.as_view(), name='ListInternetProviderAPIView'),
]
