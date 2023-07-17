from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, response, generics

from accounts.permissions import AdminPermission

from contracts.serializers import DocumentSerializer
from contracts.models import Service, Document

from main.utils import responseErrorMessage
from main.permission import ApplicationPermission
from main.models import Application, TestFileUploader
from main.serializers import (
    ApplicationSerializer, TestFileUploaderSerializer, GetFilterNotificationCountSerializer
)


class GetFilterNotificationCount(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetFilterNotificationCountSerializer

    def get(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        return response.Response(data=serializer.data, status=status.HTTP_200_OK)


class TestFileUploaderView(generics.ListCreateAPIView):
    queryset = TestFileUploader.objects.all()
    serializer_class = TestFileUploaderSerializer


# class DocumentCreateAPIView(generics.CreateAPIView):
#     queryset = Document.objects.all()
#     serializer_class = DocumentSerializer
#     permission_classes = (AdminPermission,)


class DocumentCreateListAPIView(generics.ListCreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    # permission_classes = (AdminPermission,)


class ApplicationCreateView(CreateAPIView):
    serializer_class = ApplicationSerializer
    queryset = Application.objects.all()

    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, service_id=self.request.data["service"])


class ApplicationListView(ListAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [ApplicationPermission]

    def get_queryset(self):
        if self.request.user.role.name in ApplicationPermission.permitted_roles:
            queryset = self.queryset.all()
        else:
            pinned_user = self.request.user

            try:
                service_pk = Service.objects.get(pinned_user=pinned_user).pk
            except Service.DoesNotExist:
                service_pk = None
                # Return an empty queryset if the user is not pinned to any service
                responseErrorMessage(
                    message="Siz Xizmat turiga biriktirilmagan siz",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            queryset = self.queryset.filter(service__pk=service_pk)
        return queryset


class ApplicationRetrieveView(RetrieveAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [ApplicationPermission]

    def get_object(self):
        obj = super(ApplicationRetrieveView, self).get_object()

        if self.request.user.role.name in ApplicationPermission.permitted_roles:
            obj = self.queryset.filter(pk=self.kwargs.get("pk")).first()
        else:
            pinned_user = self.request.user
            try:
                service_pk = Service.objects.get(pinned_user=pinned_user).pk
            except Service.DoesNotExist:
                service_pk = None
                # Return an empty queryset if the user is not pinned to any service
                responseErrorMessage(
                    message="Siz Xizmat turiga biriktirilmagan siz",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            obj = self.queryset.filter(service__pk=service_pk, pk=self.kwargs.get("pk")).first()
        if not obj:
            responseErrorMessage(
                message="Application not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return obj
