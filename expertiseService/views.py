import os
import json
import base64
import hashlib
import requests
import xmltodict
from datetime import datetime, timedelta

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from drf_yasg.utils import swagger_auto_schema

from rest_framework import response, status, decorators
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from contracts.models import Participant, Service
from contracts.tasks import file_downloader
from contracts.permission import IsAuthenticatedAndOwner
from contracts.utils import (
    NumbersToWord, render_to_pdf, error_response_500, 
    delete_file, create_qr
)

from accounts.models import YurUser, UserData
from accounts.serializers import YurUserSerializerForContractDetail

from main.models import Application
from main.utils import responseErrorMessage

from expertiseService.permission import IsRelatedToExpertiseBackOffice
from expertiseService.models import (
    AgreementStatus, ExpertiseContracts_Participants,
    ExpertiseServiceContract, ExpertiseTarifContract,
    ExpertiseServiceContractTarif, ExpertiseExpertSummary,
    ExpertisePkcs
)
from expertiseService.serializers import (
    ExpertiseServiceContractSerializers,
    ExpertiseContractSerializerForDetail,    
    ExpertiseContractParticipantsSerializers,
    ExpertiseContractSerializerForContractList,
    ExpertiseContractSerializerForBackoffice,
    ExpertiseExpertSummarySerializerForSave,
    ExpertiseSummarySerializerForRejected,
    ExpertisePkcsSerializer
)

num2word = NumbersToWord()


# Back office APIs
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
        print("date >>> ", date)
        context['datetime'] = datetime.fromisoformat(str(date)).time().strftime('%d.%m.%Y')
        print("datetime1 >>> ", datetime.fromisoformat(str(date)).time().strftime('%d.%m.%Y'))
        print("datetime2 >>> ", str(datetime.fromisoformat(str(date)).time().strftime('%d.%m.%Y')))
        print("datetime3 >>> ", context['datetime'])

        context['price'] = request_objects_serializers.validated_data.get("contract_cash")
        context['price_text'] = num2word.change_num_to_word(int(context['price']))

        context['withoutnds_price'] = float(context['price']) * 0.88
        context['withoutnds_price_text'] = num2word.change_num_to_word(int(context['withoutnds_price']))        

        context['onlynds_price'] = float(context['price']) * 0.12
        context['onlynds_price_text'] = num2word.change_num_to_word(int(context['onlynds_price']))

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
            
            if expertise_service_contract.contract_cash >= 10_000_000:
                exclude_role_name = "direktor o'rinbosari"
            else:
                exclude_role_name = "direktor"

            for participant in participants:
                if participant.role.name != exclude_role_name:
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


class ExpertiseGetGroupContract(APIView):
    permission_classes = [IsRelatedToExpertiseBackOffice]

    @decorators.cache_page(60 * 15, cache='default')
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
                Q(contract_status=5) | Q(contract_status=1)).select_related() \
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


class ExpertiseConfirmContract(APIView):
    permission_classes = (IsRelatedToExpertiseBackOffice,)

    def post(self, request):
        contract = get_object_or_404(ExpertiseServiceContract, pk=int(request.data['contract']))

        if int(request.data['summary']) == 1:  # 1 -> muofiq, 0 -> muofiq emas
            agreement_status = AgreementStatus.objects.get(name='Kelishildi')
        else:
            agreement_status = AgreementStatus.objects.get(name='Rad etildi')
            contract.contract_status = 1

        contracts_participants = ExpertiseContracts_Participants.objects.get(
                Q(role=request.user.role),
                Q(contract=contract),
                Q(participant_user=request.user)
        )

        if contracts_participants is None or contracts_participants.participant_user!=request.user:
            responseErrorMessage(
                message="you are not contract's participant",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        contracts_participants.agreement_status = agreement_status
        contracts_participants.save()

        # If the amount of the contract is more than 10 million,
        # it expects the director to give a conclusion
        director_role_name = "direktor" if contract.contract_cash >= 10_000_000 else "direktor o'rinbosari"
        try:
            cntrct = ExpertiseContracts_Participants.objects.get(
                contract=contract,
                role__name=director_role_name,
                agreement_status__name='Kelishildi'
            )
        except ExpertiseContracts_Participants.DoesNotExist:
            cntrct = None

        try:
            cntrctIqYu = ExpertiseContracts_Participants.objects.filter(
                Q(role__name="iqtisodchi") | Q(role__name="yurist"),
                contract=contract,
                agreement_status__name='Kelishildi'
            )
            cntrctDiDo = ExpertiseContracts_Participants.objects.filter(
                Q(role__name="direktor") | Q(role__name="direktor o'rinbosari"),
                contract=contract,
                agreement_status__name='Yuborilgan'
            )
        except ExpertiseContracts_Participants.DoesNotExist:
            cntrctIqYu, cntrctDiDo = None, None

        if cntrct:
            contract.contract_status = 4  # To'lov kutilmoqda
        
        if len(cntrctIqYu)==2 and len(cntrctDiDo)!=0:
            contract.contract_status = 6  # Yangi

        contract.save()

        request.data._mutable = True
        request.data['user'] = request.user.id

        try:
            documents = request.FILES.getlist('documents', None)
        except:
            documents = None

        summary = ExpertiseExpertSummarySerializerForSave(
            data=request.data, context={'documents': documents}
        )
        summary.is_valid(raise_exception=True)
        summary.save()

        return response.Response(status=200)


# Front office APIs -> client request user
class ExpertiseGetUserContracts(APIView):
    permission_classes = [IsAuthenticated]

    @decorators.cache_page(60 * 15, cache='default')
    def get(self, request):
        contracts = ExpertiseServiceContract.objects.filter(client=request.user).exclude(contract_status=0)
        serializer = ExpertiseContractSerializerForContractList(contracts, many=True)
        return response.Response(serializer.data)


# General APIs
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


class ExpertiseGetContractFile(APIView):
    permission_classes = ()

    def get(self, request, hash_code):
        if hash_code is None:
            return response.Response(data={"message": "404 not found error"}, status=status.HTTP_404_NOT_FOUND)
        contract = get_object_or_404(ExpertiseServiceContract, hashcode=hash_code)

        if contract.contract_status==4 or contract.contract_status==3:  # To'lov kutilmoqda va Aktiv
            # delete like pdf file test mode
            if contract.like_preview_pdf:
                delete_file(contract.like_preview_pdf.path)
                contract.like_preview_pdf = None
                contract.save()

            file_pdf_path, pdf_file_name = file_downloader(
                bytes(contract.base64file[2:len(contract.base64file) - 1], 'utf-8'), contract.id
            )
            if os.path.exists(file_pdf_path):
                with open(file_pdf_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/pdf")
                    response['Content-Disposition'] = f'attachment; filename="{pdf_file_name}"'
                    delete_file(file_pdf_path)
                    return response
        else:
            if contract.like_preview_pdf:
                # Open the file and create a response with the PDF data
                with open(contract.like_preview_pdf.path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={contract.contract_number}.pdf'
                    return response

        return response.Response(data={"message": "404 not found error"}, status=status.HTTP_404_NOT_FOUND)


# Agar client sharnomani rejected qilsa
class ExpertiseContractRejectedViews(APIView):
    serializer_class = ExpertiseSummarySerializerForRejected
    permission_classes = [IsAuthenticatedAndOwner]

    @swagger_auto_schema(operation_summary="Front Officeda Expertisada. clientga yaratilgan shartnomani bekor qilish uchun")
    def post(self, request, contract_id):
        contract = get_object_or_404(ExpertiseServiceContract, pk=contract_id)
        self.check_object_permissions(self.request, contract)
        if contract.contract_status != 5:  # Bekor qilingan
            serializer = self.serializer_class(data=request.data)

            serializer.is_valid(raise_exception=True)
            contract.contract_status = 5  # Bekor qilingan
            contract.save()

            serializer.save(
                summary=0,
                user=request.user,
                contract=contract,
                user_role=request.user.role
            )
            return response.Response({
                "message": f"Rejected Contract id: {contract_id}"
                },status=201
            )
        responseErrorMessage(
            message="you are already rejected contract",
            status_code=200
        )


class ExpertiseSavePkcs(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ExpertisePkcsSerializer

    def join2pkcs(self, pkcs7_1, pkcs7_2):
        xml = f"""
            <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                <Body>
                    <join2Pkcs7Attached xmlns="http://v1.pkcs7.plugin.server.dsv.eimzo.yt.uz/">
                        <pkcs7AttachedB64A xmlns="">{pkcs7_1}</pkcs7AttachedB64A>
                        <pkcs7AttachedB64B xmlns="">{pkcs7_2}</pkcs7AttachedB64B>
                    </join2Pkcs7Attached>
                </Body>
            </Envelope>
            """
        headers = {'Content-Type': 'text/xml'}  # set what your server accepts
        res = requests.post('http://dsv-server-vpn-client:9090/dsvs/pkcs7/v1',
                            data=xml, headers=headers)
        dict_data = xmltodict.parse(res.content)
        pkcs7_12 = dict_data['S:Envelope']['S:Body']['ns2:join2Pkcs7AttachedResponse']['return']
        d = json.loads(pkcs7_12)
        return d

    def verifyPkcs(self, pkcs):
        xml = f"""
            <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                <Body>
                    <verifyPkcs7 xmlns="http://v1.pkcs7.plugin.server.dsv.eimzo.yt.uz/">
                        <pkcs7B64 xmlns="">{pkcs}</pkcs7B64>
                    </verifyPkcs7>
                </Body>
            </Envelope>
        """
        headers = {'Content-Type': 'text/xml'}  # set what your server accepts
        res = requests.post('http://dsv-server-vpn-client:9090/dsvs/pkcs7/v1',
                            data=xml, headers=headers)
        dict_data = xmltodict.parse(res.content)
        response = dict_data['S:Envelope']['S:Body']['ns2:verifyPkcs7Response']['return']
        d = json.loads(response)
        return d

    def post(self, request):
        contract_id = int(request.data['contract_id'])
        pkcs7 = request.data['pkcs7']
        try:
            contract = ExpertiseServiceContract.objects.get(pk=contract_id)
            if request.user.role in ExpertiseContracts_Participants.objects.filter(contract=contract).values('role'):
                if not ExpertisePkcs.objects.filter(contract=contract).exists():
                    pkcs = ExpertisePkcs.objects.create(contract=contract, pkcs7=pkcs7)
                    pkcs.save()
                else:
                    pkcs_exist_object = ExpertisePkcs.objects.get(contract=contract)
                    client_pkcs = pkcs_exist_object.pkcs7
                    new_pkcs7 = self.join2pkcs(pkcs7, client_pkcs)
                    pkcs_exist_object.pkcs7 = new_pkcs7
                    pkcs_exist_object.save()
        except ExpertiseServiceContract.DoesNotExist:
            return response.Response({'message': 'Bunday shartnoma mavjud emas'})
        return response.Response({'message': 'Success'})
