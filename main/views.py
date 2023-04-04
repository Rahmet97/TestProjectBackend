from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, response, generics

from main.utils import responseErrorMessage
from main.permission import IsAndPinnedToService, PERMITED_ROLES
from .models import Application
from contracts.models import Service
from .serializers import ApplicationSerializer


class ApplicationCreateView(CreateAPIView):
    serializer_class = ApplicationSerializer
    queryset = Application.objects.all()
    
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, service_id=self.request.data["service"])


class ApplicationListView(ListAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAndPinnedToService, IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role.name in PERMITED_ROLES:
            queryset = self.queryset.all()
        else:
            pinned_user = self.request.user

            try:
                service_pk = Service.objects.get(pinned_user=pinned_user).pk
            except Service.DoesNotExist:
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
    permission_classes = [IsAuthenticated, IsAndPinnedToService]
    
    def get_object(self):
        obj = super(ApplicationRetrieveView, self).get_object()

        if self.request.user.role.name in PERMITED_ROLES:
            obj = self.queryset.filter(pk=self.kwargs.get("pk")).first()
        else:
            pinned_user = self.request.user
            try:
                service_pk = Service.objects.get(pinned_user=pinned_user).pk
            except Service.DoesNotExist:
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
