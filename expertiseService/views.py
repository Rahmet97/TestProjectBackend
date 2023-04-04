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
from contracts.models import Participant, Service
from contracts.utils import NumbersToWord, render_to_pdf, error_response_500, delete_file

from accounts.models import YurUser, UserData
from accounts.serializers import YurUserSerializerForContractDetail

from main.models import Application
from main.utils import responseErrorMessage

from expertiseService.permission import IsRelatedToExpertiseBackOffice
from expertiseService.models import (
    AgreementStatus, ExpertiseContracts_Participants,
    ExpertiseServiceContract, ExpertiseTarifContract, ExpertiseServiceContractTarif, ExpertiseExpertSummary
)
from expertiseService.serializers import (
    ExpertiseServiceContractSerializers,
    ExpertiseContractSerializerForDetail,    
    ExpertiseContractParticipantsSerializers,
    ExpertiseContractSerializerForContractList,
    ExpertiseContractSerializerForBackoffice
)

num2word = NumbersToWord()


class CreateExpertiseServiceContractView(APIView):
    queryset = ExpertiseServiceContract.objects.all()
    permission_classes = [IsAuthenticated]

    def generate_hash_code(self, text: str):
        hashcode = hashlib.md5(text.encode())
        hash_code = hashcode.hexdigest()
        return hash_code
    
    def create_contract_participants(self, service_id: int):
        participants = Participant.objects.get(service_id=service_id).participants.all()
        users = []
        service_group = Service.objects.get(id=service_id).group
        for role in participants:

            query = Q(role=role) & (Q(group=service_group) | Q(group=None))
            
            try:
                matching_user = UserData.objects.get(query)
                print(f"User {matching_user.id}: {matching_user.role.name}")
                
                users.append(matching_user)
            except UserData.DoesNotExist:
                print("No matching user found")
            except UserData.MultipleObjectsReturned:
                print("Multiple matching users found")

        return users

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

            if contract_file_for_base64_pdf is None:
                error_response_500()

            # -------
            contract_file = open(contract_file_for_base64_pdf, 'rb').read()
            base64code = base64.b64encode(contract_file)

            agreement_status = AgreementStatus.objects.filter(name='Yuborilgan').first()

            # pdf fileni ochirish
            delete_file(contract_file_for_base64_pdf)
            # qr_code fileni ochirish
            delete_file(qr_code_path)

            # -------
            # preview ni bazaga ham saqlab ketishim kk chunki contractni statusiga qarab foydalanish uchun
            context['save'] = False
            like_preview_pdf = render_to_pdf(template_src=template_name, context_dict=context)
            like_preview_pdf_path = None
            if like_preview_pdf:
                output_dir = '/usr/src/app/media/Contract/pdf'
                os.makedirs(output_dir, exist_ok=True)
                like_preview_pdf_path = f"{output_dir}/{context.get('contract_number')}_{context.get('user_obj').get_director_short_full_name}.pdf"
                with open(like_preview_pdf_path, 'wb') as f:
                    f.write(like_preview_pdf.content)
            elif like_preview_pdf_path is None:
                error_response_500()
            else:
                error_response_500()

            projects_data = request_objects_serializers.validated_data.pop('projects')
            user_stir = request_objects_serializers.validated_data.pop('stir')
            print(135, type(projects_data))
            print(136, projects_data)
            client = UserData.objects.get(username=user_stir)

            # Script code ni togirlash kk
            expertise_service_contract = ExpertiseServiceContract.objects.create(
                **request_objects_serializers.validated_data,
                
                service_id=int(request.data['service_id']),
                client=client,
                status=4,
                contract_status=0,

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

            # ExpertiseContracts_Participants
            service_id=int(request.data['service'])

            # test mode
            participants = self.create_contract_participants(service_id=service_id)
            for participant in participants:
                print(participant)
                ExpertiseContracts_Participants.objects.create(
                    contract=expertise_service_contract,
                    role=participant.role,
                    participant_user=participant,
                    agreement_status=agreement_status
                ).save()

            # Contract yaratilgandan so'ng application ni is_contracted=True qilib qo'yish kk 
            application_pk = request.data.get("application_pk")
            Application.objects.filter(pk=application_pk).update(is_contracted=True)

            return response.Response(data={"message": "Created Expertise Service Contract"}, status=201)

        template_name = "shablonEkspertiza.html"
        return render(request=request, template_name=template_name, context=context)


class ExpertiseContractDetail(APIView):
    permission_classes = (IsAuthenticated,)
    permitted_roles = ["direktor o'rinbosari", "direktor", "iqtisodchi", "yurist", "dasturchi"]

    def get(self, request, pk):
        contract = ExpertiseServiceContract.objects.select_related('client').get(pk=pk)
        contract_serializer = ExpertiseContractSerializerForDetail(contract)

        # agar request user mijoz bo'lsa
        # expertise model yaratilganidan keyin statusi ozgarishi kk front ofise uchun
        # yani iqtisodchi va yurist dan otganidan keyin
        if (request.user.role.name == "mijoz" and \
            contract.client == request.user and \
            contract.contract_status==6):
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
        participants = ExpertiseContracts_Participants.objects.filter(contract=contract).order_by('role_id')
        print("participants >>> ", participants)
        participant_serializer = ExpertiseContractParticipantsSerializers(participants, many=True)

        try:
            expert_summary_value = ExpertiseExpertSummary.objects.get(
                Q(contract=contract), Q(user=request.user),
                (Q(user__group=request.user.group) | Q(user__group=None))
            ).summary

        except ExpertiseExpertSummary.DoesNotExist:
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
        contracts = ExpertiseServiceContract.objects.filter(
            client=request.user, contract_status=6
        )
        serializer = ExpertiseContractSerializerForContractList(contracts, many=True)
        return response.Response(serializer.data)


class ExpertiseGetGroupContract(APIView):
    permission_classes = [IsRelatedToExpertiseBackOffice]

    def get(self, request):

        # yangi contractlar
        if request.user.role.name == 'direktor':
            contract_participants = ExpertiseContracts_Participants.objects.filter(
                Q(role__name="direktor o'rinbosari"),
                Q(agreement_status__name='Kelishildi')
            ).values('contract')

            director_accepted_contracts = ExpertiseContracts_Participants.objects.filter(
                Q(role__name='direktor'), Q(agreement_status__name='Kelishildi')
            ).values('contract')

            yangi_data = ExpertiseServiceContract.objects.filter(id__in=contract_participants).exclude(
                Q(id__in=director_accepted_contracts),
                Q(contract_status=5),
                Q(contract_status=1)).select_related().order_by('-contract_date')
        else:
            contract_participants = ExpertiseContracts_Participants.objects.filter(
                Q(role=request.user.role),
                (Q(agreement_status__name='Yuborilgan') |
                    Q(agreement_status__name="Ko'rib chiqilmoqda"))
            ).values('contract')
            yangi_data = ExpertiseServiceContract.objects.filter(id__in=contract_participants).exclude(
                Q(contract_status="Bekor qilingan") | Q(contract_status=1)).select_related() \
                .order_by('-contract_date')
        self.check_object_permissions(request=request, obj=yangi_data)
        yangi = ExpertiseContractSerializerForBackoffice(yangi_data, many=True)

        # kelishilgan contractlar
        contract_participants = ExpertiseContracts_Participants.objects.filter(
            Q(role=request.user.role),
            Q(agreement_status__name='Kelishildi')
        ).values('contract')
        kelishilgan_data = ExpertiseServiceContract.objects.filter(
            id__in=contract_participants
        ).select_related().order_by('-contract_date')
        self.check_object_permissions(request=request, obj=kelishilgan_data)
        kelishilgan = ExpertiseContractSerializerForBackoffice(kelishilgan_data, many=True)

        # rad etilgan contractlar
        rad_etildi_data = ExpertiseServiceContract.objects.filter(
            (Q(contract_status=5) | Q(contract_status=1))
        ).order_by('-contract_date')
        self.check_object_permissions(request=request, obj=rad_etildi_data)
        rad_etildi = ExpertiseContractSerializerForBackoffice(rad_etildi_data, many=True)

        # expired contracts
        contract_participants = ExpertiseContracts_Participants.objects.filter(
            Q(role=request.user.role),
            (Q(agreement_status__name='Yuborilgan') |
                Q(agreement_status__name="Ko'rib chiqilmoqda"))
        ).values('contract')
        expired_data = ExpertiseServiceContract.objects.filter(
            Q(id__in=contract_participants),
            Q(contract_date__lt=datetime.now() - timedelta(days=1))).select_related().order_by('-contract_date')
        self.check_object_permissions(request=request, obj=expired_data)
        expired = ExpertiseContractSerializerForBackoffice(expired_data, many=True)

        # last day contractlar
        contract_participants = ExpertiseContracts_Participants.objects.filter(
            Q(role=request.user.role),
            (Q(agreement_status__name='Yuborilgan') |
                Q(agreement_status__name="Ko'rib chiqilmoqda"))
        ).values('contract')
        lastday_data = ExpertiseServiceContract.objects.filter(
            Q(id__in=contract_participants),
            Q(contract_date__day=datetime.now().day),
            Q(contract_date__month=datetime.now().month),
            Q(contract_date__year=datetime.now().year)).exclude(
            Q(contract_status=5) | Q(contract_status=1)).select_related() \
            .order_by('-contract_date')
        self.check_object_permissions(request=request, obj=lastday_data)
        lastday = ExpertiseContractSerializerForBackoffice(lastday_data, many=True)

        # expired accepted contracts
        contract_participants = ExpertiseContracts_Participants.objects.filter(
            Q(role=request.user.role),
            Q(agreement_status__name='Kelishildi')
        ).values('contract')
        expired_accepted_data = ExpertiseServiceContract.objects.filter(
            Q(id__in=contract_participants),
            Q(contract_date__lt=datetime.now() - timedelta(days=1))
        ).select_related().order_by('-contract_date')
        self.check_object_permissions(request=request, obj=expired_accepted_data)
        expired_accepted = ExpertiseContractSerializerForBackoffice(expired_accepted_data, many=True)

        # in_time contracts
        contracts_selected = ExpertiseExpertSummary.objects.select_related('contract').filter(
            Q(user=request.user)
        ).order_by('-contract', '-contract__contract_date')
        in_time_data = [element.contract for element in contracts_selected if
                        element.contract.contract_date < element.date <= element.contract.contract_date + timedelta(days=1)]
        self.check_object_permissions(request=request, obj=in_time_data)
        in_time = ExpertiseContractSerializerForBackoffice(in_time_data, many=True)

        # barcha contractlar
        barcha_data = ExpertiseServiceContract.objects.all().order_by('-contract_date')
        self.check_object_permissions(request=request, obj=barcha_data)
        barcha = ExpertiseContractSerializerForBackoffice(barcha_data, many=True)

        return response.Response(
            data = {
                'barcha': barcha.data,
                'yangi': yangi.data,
                'kelishildi': kelishilgan.data,
                'rad_etildi': rad_etildi.data,
                'expired': expired.data,
                'lastday': lastday.data,
                'expired_accepted': expired_accepted.data,
                'in_time': in_time.data
            },
            status=200
        )
