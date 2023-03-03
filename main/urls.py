from django.urls import path
from main import views


urlpatterns = [
    path("send-message", views.ApplicationCreateView.as_view(), name="send-message")
]
