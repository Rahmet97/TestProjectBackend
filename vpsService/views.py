from rest_framework import views, generics, permissions, response, status

from main.utils import responseErrorMessage
from .models import (
    VpsServiceContract,
    OperationSystem,
    OperationSystemVersion,
    VpsDevice,
    VpsTariff,
    VpsContractDevice,
    VpsContracts_Participants,
    VpsExpertSummary,
    VpsExpertSummaryDocument,
)
from .serializers import OperationSystemSerializers, OperationSystemVersionSerializers


# View for listing OperationSystem objects
class OperationSystemListView(generics.ListAPIView):
    # Retrieve all OperationSystem objects
    queryset = OperationSystem.objects.all()
    # Use OperationSystemSerializers for serialization
    serializer_class = OperationSystemSerializers

    # Specify the permission classes for this view
    permission_classes = [permissions.IsAuthenticated]


# View for listing OperationSystemVersion objects based on an operation_system_id
class OperationSystemVersionListView(views.APIView):
    # Specify the permission classes for this view
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, operation_system_id):
        # Filter OperationSystemVersion objects based on the provided operation_system_id
        operation_system_version_objects = OperationSystemVersion.objects.filter(
            operation_system__id=operation_system_id
        )

        # Check if any OperationSystemVersion objects were found
        if operation_system_version_objects.exists():
            # Serialize the queryset of OperationSystemVersion objects
            serializer = OperationSystemVersionSerializers(operation_system_version_objects, many=True)

            # Return the serialized data with a 200 OK status
            return response.Response(data=serializer.data, status=status.HTTP_200_OK)

        # If no OperationSystemVersion objects were found, raise an error
        raise responseErrorMessage(
            message="objects not found 404",
            status_code=status.HTTP_404_NOT_FOUND
        )
