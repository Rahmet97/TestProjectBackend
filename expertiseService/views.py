import os
import base64
import hashlib
from datetime import datetime, timedelta

from django.shortcuts import render
from django.db.models import Q

from rest_framework import response
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from contracts.utils import create_qr
from contracts.models import (
    Service, Status, AgreementStatus, Contracts_Participants, ContractStatus,
    Participant, Contract, ExpertiseTarifContract, ExpertiseServiceContractTarif, ExpertSummary
)
from contracts.utils import NumbersToWord, render_to_pdf, error_response_500, delete_file
from contracts.serializers import (
    ContractSerializerForDetail, 
    ContractParticipantsSerializers, 
    ContractSerializerForContractList,
    ContractSerializerForBackoffice
)

from accounts.models import YurUser, UserData
from accounts.serializers import YurUserSerializerForContractDetail

from main.models import Application
from main.utils import responseErrorMessage

from expertiseService.serializers import ExpertiseServiceContractSerializers
from expertiseService.permission import IsRelatedToExpertiseBackOffice

num2word = NumbersToWord()


class CreateExpertiseServiceContractView(GenericAPIView):
    queryset = Contract.objects.all()
    permission_classes = [IsAuthenticated]

    def generate_hash_code(self, text: str):
        hashcode = hashlib.md5(text.encode())
        hash_code = hashcode.hexdigest()
        return hash_code

    def post(self, request):
        context = dict()
        request_objects_serializers = ExpertiseServiceContractSerializers(data=request.data)
        request_objects_serializers.is_valid(raise_exception=True)

        context['u_type'] = 'yuridik'
        context["user_obj"] = YurUser.objects.get(tin=request_objects_serializers.validated_data.get("stir"))
        context['contract_number'] = request_objects_serializers.validated_data.get("contract_number")

        date = request_objects_serializers.validated_data.get("contract_date")
        context['datetime'] = datetime.fromisoformat(str(date)).time().strftime('%d.%m.%Y')

        context['price'] = request_objects_serializers.validated_data.get("contract_cash")
        context['price_text'] = num2word.change_num_to_word(int(context['price']))
        context['price_select_percentage'] = request_objects_serializers.validated_data.get('price_select_percentage')
        context['price_select_percentage_text'] = num2word.change_num_to_word(int(context['price_select_percentage']))

        context['tarif'] = request_objects_serializers.validated_data.get("projects")

        context['host'] = 'http://' + request.META['HTTP_HOST']
        context['qr_code'] = ''
        context['save'] = False
        context['page_break'] = False

        if int(request.data['save']):
            context['save'] = True
            context['page_break'] = True

            hash_code = self.generate_hash_code(
                text=f"{context.get('user_obj').get_director_short_full_name}{context.get('contract_number')}{context.get('u_type')}{datetime.now()}"
            )

            link = 'http://' + request.META['HTTP_HOST'] + f'/contracts/contract/{hash_code}'
            qr_code_path = create_qr(link)
            context['hash_code'] = hash_code
            context['qr_code'] = f"http://api.unicon.uz/media/qr/{hash_code}.png"

            # -------
            # rendered html file
            contract_file_for_base64_pdf = None

            template_name = "shablonEkspertiza.html"
            pdf = render_to_pdf(template_src=template_name, context_dict=context)
            if pdf:
                output_dir = '/usr/src/app/media/Contract/pdf'
                os.makedirs(output_dir, exist_ok=True)
                contract_file_for_base64_pdf = f"{output_dir}/{context.get('contract_number')}_{context.get('user_obj').get_director_short_full_name}.pdf"
                with open(contract_file_for_base64_pdf, 'wb') as f:
                    f.write(pdf.content)
            else:
                error_response_500()

            if contract_file_for_base64_pdf == None:
                error_response_500()

            # -------
            contract_file = open(contract_file_for_base64_pdf, 'rb').read()
            base64code = base64.b64encode(contract_file)

            status = Status.objects.filter(name='Yangi').first()
            contract_status = ContractStatus.objects.filter(name='Yangi').first()
            agreement_status = AgreementStatus.objects.filter(name='Yuborilgan').first()

            # pdf fileni ochirish
            delete_file(contract_file_for_base64_pdf)
            # qr_code fileni ochirish
            delete_file(qr_code_path)

            # -------
            # preview ni bazaga ham saqlab ketishim kk chunki contractni statusiga qarab foydalanish uchun
            context['save'] = False
            like_preview_pdf = render_to_pdf(template_src=template_name, context_dict=context)
            if like_preview_pdf:
                output_dir = '/usr/src/app/media/Contract/pdf'
                os.makedirs(output_dir, exist_ok=True)
                like_preview_pdf_path = f"{output_dir}/{context.get('contract_number')}_{context.get('user_obj').get_director_short_full_name}.pdf"
                with open(like_preview_pdf_path, 'wb') as f:
                    f.write(like_preview_pdf.content)
            elif like_preview_pdf_path == None:
                error_response_500()
            else:
                error_response_500()

            projects_data = request_objects_serializers.validated_data.pop('projects')
            user_stir = request_objects_serializers.validated_data.pop('stir')

            client = UserData.objects.get(username=user_stir)

            # Script code ni togirlash kk
            expertise_service_contract = Contract.objects.create(
                **request_objects_serializers.validated_data,

                client=client,
                status=status,
                contract_status=contract_status,

                payed_cash=0,
                base64file=base64code,
                hashcode=hash_code,
                like_preview_pdf=like_preview_pdf_path
            )
            expertise_service_contract.save()

            for project_data in projects_data:
                project = ExpertiseServiceContractTarif.objects.create(**project_data)
                ExpertiseTarifContract.objects.create(
                    contract=expertise_service_contract,
                    tarif=project
                )

            participants = Participant.objects.get(service_id=int(request.data['service'])).participants.all()
            for participant in participants:
                print(participant)
                Contracts_Participants.objects.create(
                    contract=expertise_service_contract,
                    role=participant,
                    agreement_status=agreement_status
                ).save()
            
            # Contract yaratilgandan so'ng application ni is_contracted=True qilib qo'yish kk 
            application_pk = request.data.get("application_pk")
            Application.objects.filter(pk=application_pk).update(is_contracted=True)

            return response.Response(data={"message": "Created Expertise Service Contract"}, status=201)

        template_name="shablonEkspertiza.html"
        return render(request=request, template_name=template_name, context=context)


# class ExpertiseContractDetail(APIView):
#     permission_classes = (IsAuthenticated, )

#     def get(self, request, pk):
#         contract = Contract.objects.select_related('client').get(pk=pk)
#         contract_serializer = ContractSerializerForDetail(contract)

#         try:
#             contract_participants = Contracts_Participants.objects.filter(
#                 contract=contract
#             ).get(
#                 (Q(role=request.user.role) & Q(contract__service__group=request.user.group)) |
#                 Q(role__name='direktor') | Q(role__name='iqtisodchi') | Q(role__name='yurist')
#             )
#         except Contracts_Participants.DoesNotExist:
#             contract_participants = None

#         if (request.user.role.name == "dasturchi") \
#             or (request.user.role.name == "direktor o'rinbosari") \
#             or (request.user.role.name == "direktor") \
#             or (request.user.role.name == "iqtisodchi") \
#             or (request.user.role.name == "yurist") \
#             and (contract_participants.agreement_status.name == "Yuborilgan"):

#             agreement_status = AgreementStatus.objects.get(name="Ko'rib chiqilmoqda")
#             contract_participants.agreement_status = agreement_status
#             contract_participants.save()

#         user = YurUser.objects.get(userdata=contract.client)
#         client_serializer = YurUserSerializerForContractDetail(user)

#         participants = Contracts_Participants.objects.filter(contract=contract).order_by('role_id')
#         participant_serializer = ContractParticipantsSerializers(participants, many=True)

#         try:
#             expert_summary_value = ExpertSummary.objects.get(
#                 Q(contract=contract),
#                 Q(user=request.user),
#                 (Q(user__group=request.user.group)|Q(user__group=None))
#             ).summary
#         except ExpertSummary.DoesNotExist:
#             expert_summary_value = 0

#         return response.Response(data={
#                 'contract': contract_serializer.data,
#                 'client': client_serializer.data,
#                 'participants': participant_serializer.data,
#                 'is_confirmed': True if int(expert_summary_value) == 1 else False
#             },
#             status=200
#         )


class ExpertiseContractDetail(APIView):
    permission_classes = (IsAuthenticated,)
    permitted_roles = ["direktor o'rinbosari", "direktor", "iqtisodchi", "yurist", "dasturchi"]


    def get(self, request, pk):
        contract = Contract.objects.select_related('client').get(pk=pk)
        contract_serializer = ContractSerializerForDetail(contract)

        # agar request user mijoz bo'lsa
        # expertise model yaratilganidan keyin statusi ozgarishi kk front ofise uchun
        # yani iqtisodchi va yurist dan otganidan keyin
        if request.user.role.name == "mijoz" and contract.client == request.user: # and contract.contract_status=="yangi":
            client = request.user

        # agar reuqest user direktor, direktor o'rin bosari bo'lsa
        # agar reuqest user iqtisodchi, yurist yoki dasturchi bo'lsa
        elif request.user.role.name in self.permitted_roles:
            client = contract.client

        else:
            responseErrorMessage(
                message="You are not permitted to view this contact detail", 
                status_code=200
            )
        
        user = YurUser.objects.get(userdata=client)
        client_serializer = YurUserSerializerForContractDetail(user)
        participants = Contracts_Participants.objects.filter(contract=contract).order_by('role_id')
        participant_serializer = ContractParticipantsSerializers(participants, many=True)

        try:
            expert_summary_value = ExpertSummary.objects.get(
                Q(contract=contract), Q(user=request.user),
                (Q(user__group=request.user.group)|Q(user__group=None))
            ).summary

        except ExpertSummary.DoesNotExist:
            expert_summary_value = 0

        return response.Response(data={
                'contract': contract_serializer.data,
                'client': client_serializer.data,
                'participants': participant_serializer.data,
                'is_confirmed': True if int(expert_summary_value) == 1 else False
            },
            status=200
        )


# client request user
class ExpertiseGetUserContracts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contracts = Contract.objects.filter(
            client=request.user
        ).exclude()
        serializer = ContractSerializerForContractList(contracts, many=True)
        return response.Response(serializer.data)

class ExpertiseGetGroupContract(APIView):
    permission_classes = [IsRelatedToExpertiseBackOffice]

    def get(self, request):
        group = request.user.group
        if request.user.role.name != "mijoz":

            contracts = None
            barcha_data = Contract.objects.filter(
                service__group=group).order_by('-condition', '-contract_date')
            barcha = ContractSerializerForBackoffice(barcha_data, many=True)
            if request.user.role.name == 'direktor':
                contract_participants = Contracts_Participants.objects.filter(
                    (Q(contract__service__group=group) | Q(contract__service__group=None)),
                    Q(role__name="direktor o'rinbosari"),
                    Q(agreement_status__name='Kelishildi')
                ).values('contract')
                director_accepted_contracts = Contracts_Participants.objects.filter(
                    Q(role__name='direktor'), Q(
                        agreement_status__name='Kelishildi')
                ).values('contract')
                yangi_data = Contract.objects.filter(id__in=contract_participants).exclude(
                    Q(id__in=director_accepted_contracts),
                    Q(contract_status__name="Bekor qilingan"),
                    Q(contract_status__name="Rad etilgan")).select_related().order_by('-condition', '-contract_date')
            else:
                contract_participants = Contracts_Participants.objects.filter(
                    Q(contract__service__group=group),
                    Q(role=request.user.role),
                    (Q(agreement_status__name='Yuborilgan') |
                     Q(agreement_status__name="Ko'rib chiqilmoqda"))
                ).values('contract')
                yangi_data = Contract.objects.filter(id__in=contract_participants).exclude(
                    Q(contract_status__name="Bekor qilingan") | Q(contract_status__name="Rad etilgan")).select_related() \
                    .order_by('-condition', '-contract_date')
            yangi = ContractSerializerForBackoffice(yangi_data, many=True)
            contract_participants = Contracts_Participants.objects.filter(
                Q(contract__service__group=group),
                Q(role=request.user.role),
                Q(agreement_status__name='Kelishildi')
            ).values('contract')
            kelishilgan_data = Contract.objects.filter(id__in=contract_participants).select_related() \
                .order_by('-condition', '-contract_date')
            kelishilgan = ContractSerializerForBackoffice(
                kelishilgan_data, many=True)
            rad_etildi_data = Contract.objects.filter(Q(service__group=group),
                                                      (Q(contract_status__name='Bekor qilingan') | Q(
                                                          contract_status__name="Rad etilgan"))) \
                .order_by('-condition', '-contract_date')
            rad_etildi = ContractSerializerForBackoffice(
                rad_etildi_data, many=True)
            contract_participants = Contracts_Participants.objects.filter(
                Q(contract__service__group=group),
                Q(role=request.user.role),
                (Q(agreement_status__name='Yuborilgan') |
                 Q(agreement_status__name="Ko'rib chiqilmoqda"))
            ).values('contract')
            expired_data = Contract.objects.filter(
                Q(id__in=contract_participants),
                Q(contract_date__lt=datetime.now() - timedelta(days=1))).select_related().order_by('-condition', '-contract_date')
            expired = ContractSerializerForBackoffice(expired_data, many=True)
            contract_participants = Contracts_Participants.objects.filter(
                Q(contract__service__group=group),
                Q(role=request.user.role),
                (Q(agreement_status__name='Yuborilgan') |
                 Q(agreement_status__name="Ko'rib chiqilmoqda"))
            ).values('contract')
            lastday_data = Contract.objects.filter(
                Q(id__in=contract_participants),
                Q(contract_date__day=datetime.now().day),
                Q(contract_date__month=datetime.now().month),
                Q(contract_date__year=datetime.now().year)).exclude(
                Q(contract_status__name='Bekor qilingan') | Q(contract_status__name='Rad etilgan')).select_related() \
                .order_by('-condition', '-contract_date')
            lastday = ContractSerializerForBackoffice(lastday_data, many=True)
            contract_participants = Contracts_Participants.objects.filter(
                Q(contract__service__group=group),
                Q(role=request.user.role),
                Q(agreement_status__name='Kelishildi')
            ).values('contract')
            expired_accepted_data = Contract.objects.filter(
                Q(id__in=contract_participants),
                Q(contract_date__lt=datetime.now() - timedelta(days=1))
            ).select_related().order_by('-condition', '-contract_date')
            expired_accepted = ContractSerializerForBackoffice(
                expired_accepted_data, many=True)
            contracts_selected = ExpertSummary.objects.select_related('contract').filter(
                Q(user=request.user)).order_by('-contract__condition', '-contract__contract_date')
            in_time_data = [element.contract for element in contracts_selected if
                            element.contract.contract_date < element.date <= element.contract.contract_date + timedelta(
                                days=1)]
            in_time = ContractSerializerForBackoffice(in_time_data, many=True)
            contracts = {
                'barcha': barcha.data,
                'yangi': yangi.data,
                'kelishildi': kelishilgan.data,
                'rad_etildi': rad_etildi.data,
                'expired': expired.data,
                'lastday': lastday.data,
                'expired_accepted': expired_accepted.data,
                'in_time': in_time.data
            }
            return response.Response(contracts)
        else:
            contracts = Contract.objects.filter(
                Q(service__group=group), Q(condition=3))
            serializer = ContractSerializerForBackoffice(contracts, many=True)
            return response.Response(serializer.data)
