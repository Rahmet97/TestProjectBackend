from django.urls import path

from . import views


urlpatterns = [
    path('operations-systems-list/', views.OperationSystemListView.as_view(), name="operations-systems-list"),
    path(
        'operations-systems-version-list/<str:operation_system_id>',
        views.OperationSystemVersionListView.as_view(), name="operations-systems-version-list"
    ),
]
