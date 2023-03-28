from django.urls import path
from expertiseService import views


urlpatterns = [
    path("create/expertise/contract", 
         views.CreateExpertiseServiceContractView.as_view(),
         name="create-expertise-contract"
    ),
]
