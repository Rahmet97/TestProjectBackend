from django.urls import path
from .views import GetRackInfo, RackAPIView, RackDetailAPIView


urlpatterns = [
    path('rack', RackAPIView.as_view(), name='RackAPIView'),
    path('get-info', GetRackInfo.as_view(), name='GetRackInfo'),
    path('rack-detail', RackDetailAPIView.as_view(), name='RackDetailAPIView'),
]