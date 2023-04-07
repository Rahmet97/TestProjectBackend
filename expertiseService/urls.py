from django.urls import path
from expertiseService import views


urlpatterns = [
    # Endpoint to create a new expertise service contract
    path("create/expertise/contract",
         views.CreateExpertiseServiceContractView.as_view(),
         name="create-expertise-contract"),

    # Endpoint to get details of an expertise service contract by its primary key
    path('contract-detail/<int:pk>', views.ExpertiseContractDetail.as_view(),
         name='ExpertiseContractDetail'),

    # Endpoint to get all expertise service contracts that the authenticated user is a participant in
    path('user-contracts', views.ExpertiseGetUserContracts.as_view(),
         name='ExpertiseGetUserContracts'),

    # Endpoint to get all expertise service contracts for a particular group
    path('group-contracts', views.ExpertiseGetGroupContract.as_view(),
         name='ExpertiseGetGroupContract'),

    # Endpoint to confirm an expertise service contract
    path('confirm-contract', views.ExpertiseConfirmContract.as_view(),
         name='ExpertiseConfirmContract'),

    # Endpoint to get the contract file by its hash code
    path('contract/<str:hash_code>', views.ExpertiseGetContractFile.as_view(),
         name='ExpertiseGetContractFile'),

    # For Front Office. to cancel the contract created with the client
    path('contract-rejected/<int:contract_id>', views.ExpertiseContractRejectedViews.as_view(),
         name="ExpertiseContractRejectedViews"),
]
