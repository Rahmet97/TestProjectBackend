from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, response, generics

from main.utils import responseErrorMessage
from main.permission import IsAndPinnedToService
from .models import Application
from contracts.models import Service
from .serializers import ApplicationSerializer


class ApplicationCreateView(CreateAPIView):
    serializer_class = ApplicationSerializer
    queryset = Application.objects.all()
    
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ApplicationListRetrieveView(generics.GenericAPIView):
    serializer_class = ApplicationSerializer
    queryset = Application.objects.all()
    
    permission_classes = [IsAndPinnedToService]
    
    def get_object(self):
        pinned_user = self.request.user
        if not Service.objects.filter(pinned_user=pinned_user).exists():
            return responseErrorMessage(
                message="Siz Xizmat turiga biriktirilmagan siz", 
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        service_pk = Service.objects.get(pinned_user=pinned_user).pk
        queryset = self.queryset.filter(service__pk=service_pk)
        # if self.kwargs.get("pk") is not None:
        #     queryset = queryset.get(pk=self.kwargs["pk"])
        # obj = get_object_or_404(queryset)
        self.check_object_permissions(self.request, queryset)
        return queryset
    
    # def get(self, request, pk=None):
    #     if pk is not None:
    #         serializer = self.serializer_class(self.get_object, many=True)
    #     else:
    #         serializer = self.serializer_class(self.get_object)
    #     return response.Response(serializer.data, status=status.HTTP_200_OK)

    def get(self, request, pk=None):
        queryset = self.get_object()
        if pk is not None:
            serializer = self.serializer_class(queryset.get(pk=pk))
        else:
            serializer = self.serializer_class(queryset, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class ApplicationListView(ListAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAndPinnedToService, IsAuthenticated]

    # def get_object(self):
    #     pinned_user = self.request.user
        
    #     try:
    #         service_pk = Service.objects.get(pinned_user=pinned_user).pk
    #     except Service.DoesNotExist:
    #         # Return an empty queryset if the user is not pinned to any service
    #         responseErrorMessage(
    #             message="Siz Xizmat turiga biriktirilmagan siz",
    #             status_code=status.HTTP_404_NOT_FOUND
    #         )
        
    #     object.queryset = self.queryset.filter(service__pk=service_pk)
    #     return object
    
    def get_queryset(self):
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

    # def get_object(self):
    #     pinned_user = self.request.user
    #     # if not Service.objects.filter(pinned_user=pinned_user).exists():
    #     #     responseErrorMessage(
    #     #     message="Siz Xizmat turiga biriktirilmagan siz", 
    #     #     status_code=status.HTTP_404_NOT_FOUND
    #     # )

    #     try:
    #         service_pk = Service.objects.get(pinned_user=pinned_user).pk
    #     except Service.DoesNotExist:
    #         # Return an empty queryset if the user is not pinned to any service
    #         responseErrorMessage(
    #             message="Siz Xizmat turiga biriktirilmagan siz",
    #             status_code=status.HTTP_404_NOT_FOUND
    #         )
        
    #     # service_pk = Service.objects.get(pinned_user=pinned_user).pk

    #     object.queryset = self.queryset.get(service__pk=service_pk, pk=self.kwargs.get("pk"))
    #     return object
    
    def get_object(self):
        obj = super(ApplicationRetrieveView, self).get_object()
        
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
        