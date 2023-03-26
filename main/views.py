from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, response, generics

from main.utils import responseErrorMessage
from main.permission import IsAuthenticatedAndPinnedToService
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
    
    permission_classes = [IsAuthenticatedAndPinnedToService]

    def get_object(self):
        pinned_user = self.request.user
        if not Service.objects.filter(pinned_user=pinned_user).exists():
            responseErrorMessage(
            message="Siz Xizmat turiga biriktirilmagan siz", 
            status_code=status.HTTP_404_NOT_FOUND
        )
        
        service_pk = Service.objects.get(pinned_user=pinned_user).pk
        object = super(ApplicationListRetrieveView, self).get_object(self.queryset)
        if self.kwargs["pk"]:
            object.queryset = self.queryset.filter(service__pk=service_pk, pk=self.kwargs["pk"]).first()
        else:
            object.queryset = self.queryset.filter(service__pk=service_pk)
        return object
    
    def get(self, request):
        serializer = self.serializer_class(self.get_object, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
     


# class ApplicationListView(ListAPIView):
#     queryset = Application.objects.all()
#     serializer_class = ApplicationSerializer
#     permission_classes = [IsAuthenticatedAndPinnedToService]

#     def get_object(self):
#         pinned_user = self.request.user
#         if not Service.objects.filter(pinned_user=pinned_user).exists():
#             responseErrorMessage(
#             message="Siz Xizmat turiga biriktirilmagan siz", 
#             status_code=status.HTTP_404_NOT_FOUND
#         )
        
#         service_pk = Service.objects.get(pinned_user=pinned_user).pk
#         object = super(ApplicationListView, self).get_object(self.queryset)
#         object.queryset = self.queryset.filter(service__pk=service_pk)
#         return object
        