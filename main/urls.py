from django.urls import path, include
from main import views

urlpatterns = [
    path("send-message", views.ApplicationCreateView.as_view(), name="send-message"),

    # List all applications for the pinned user's service
    path("application/list/", views.ApplicationListView.as_view(), name="application-list"),

    # Retrieve a single application by its pk
    path("application/detail/<int:pk>/", views.ApplicationRetrieveView.as_view(), name="application-detail"),

    # Need Document Create and List api
    path('document-create-list', views.DocumentCreateListAPIView.as_view(), name='DocumentCreateListAPIView'),

    path('wordapp/', include('main.wordapp.urls')),
]
