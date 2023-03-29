import os
import base64
import hashlib
from datetime import datetime

from django.shortcuts import render

from rest_framework import response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from contracts.utils import create_qr
from contracts.models import (
    Service, Status, AgreementStatus, Contracts_Participants, ContractStatus,
    Participant, Contract, ExpertiseTarifContract, ExpertiseServiceContractTarif
)
from accounts.models import YurUser, UserData
from contracts.utils import NumbersToWord, render_to_pdf, error_response_500, delete_file

from expertiseService.serializers import ExpertiseServiceContractSerializers
from main.models import Application

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
        context['datetime'] = request_objects_serializers.validated_data.get("contract_date")

        context['price'] = request_objects_serializers.validated_data.get("contract_cash")
        context['price_text'] = num2word.change_num_to_word(int(context['price']))

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
                like_preview_pdf_path = f"{output_dir}/{context.get('contract_number')}_{context.get('client_fullname')}.pdf"
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
