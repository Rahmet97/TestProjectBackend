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


class OperationSystemListView(generics.ListAPIView):
    queryset = OperationSystem.objects.all()
    serializer_class = OperationSystemSerializers
    # permission_classes = [permissions.IsAuthenticated]


class OperationSystemVersionListView(views.APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, operation_system_id):
        operation_system_version_objects = OperationSystemVersion.objects.filter(
            operation_system__id=operation_system_id
        )
        if operation_system_version_objects.exists():
            serializer = OperationSystemVersionSerializers(operation_system_version_objects, many=True)
            return response.Response(data=serializer.data, status=status.HTTP_200_OK)
        raise responseErrorMessage(
            message="objects not found 404",
            status_code=status.HTTP_404_NOT_FOUND
        )
