from django.urls import path
from . import views
from main.views import TestFileUploaderView

urlpatterns = [
    path("test-file-uploader", TestFileUploaderView.as_view(), name="test-file-uploader"),

]
