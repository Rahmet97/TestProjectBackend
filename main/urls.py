from django.urls import path
from main import views


urlpatterns = [
    path("send-message", views.ApplicationCreateView.as_view(), name="send-message"),
    # List all applications for the pinned user's service
    path("application/list/", views.ApplicationListRetrieveView.as_view(), name="application-list"),
    path("list/", views.ApplicationListView.as_view(), name="list"),

    # Retrieve a single application by its pk
    path("application/detail/<int:pk>/", views.ApplicationListRetrieveView.as_view(), name="application-detail"),


]
