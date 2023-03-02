from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from billing.models import BillingLog
from billing.serializers import RequestSerializer
from contracts.models import Tarif, Element, TarifLog
from contracts.serializers import TarifSerializer, ElementSerializer


class TariffCreateAPIView(CreateAPIView):
    queryset = Tarif.objects.all()
    serializer_class = TarifSerializer
    permission_classes = (IsAuthenticated,)


class TariffUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Tarif.objects.all()
    serializer_class = TarifSerializer
    permission_classes = (IsAuthenticated,)


class ElementAPIView(ListCreateAPIView):
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (IsAuthenticated,)


class ElementUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (IsAuthenticated,)


class CalculateTariffSummAPIView(APIView):
    permission_classes = ()

    @swagger_auto_schema(query_serializer=RequestSerializer)
    def post(self, request):
        rqst = RequestSerializer(request.data)
        elements = request.data['elements']
        fr = request.data['from']
        amounts = []
        total = 0
        for i in elements:
            element = Element.objects.get(pk=int(i["element"]))
            quantity = int(i["quantity"])
            amounts.append({
                'element': int(i["element"]),
                'quantity': quantity,
                'cost_without_vat': element.cost / 1.12,
                'vat': '12%',
                'amount_vat': element.cost - element.cost / 1.12,
                'cost': element.cost
            })
            total += element.cost
        data = {
            'elements': amounts,
            'total': total
        }
        # billing_log = BillingLog.objects.create(
        #     user=request.user,
        #     fr=fr,
        #     request=rqst.data,
        #     response=data
        # )
        # billing_log.save()
        return Response(data)
