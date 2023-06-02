from django.urls import path

from . import views


# Define the URL patterns
urlpatterns = [
    # URL pattern for the list of operation systems
    path('operations-systems-list/', views.OperationSystemListView.as_view(), name="operations-systems-list"),

    # URL pattern for the list of operation system versions with a dynamic operation_system_id parameter
    path(
        'operations-systems-version-list/<str:operation_system_id>',
        views.OperationSystemVersionListView.as_view(), name="operations-systems-version-list"
    ),
]
