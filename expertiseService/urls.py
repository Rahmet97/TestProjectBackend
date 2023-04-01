from django.urls import path
from expertiseService import views


urlpatterns = [
    path("create/expertise/contract", 
         views.CreateExpertiseServiceContractView.as_view(),
         name="create-expertise-contract"
    ),

    path('contract-detail/<int:pk>', views.ExpertiseContractDetail.as_view(), name='ExpertiseContractDetail'),

    path('user-contracts', views.ExpertiseGetUserContracts.as_view(), name='GetUserContracts'),
    path('group-contracts', views.ExpertiseGetGroupContract.as_view(), name='GetGroupContract'),
]
