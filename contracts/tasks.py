import base64
import subprocess
import os

from celery import shared_task
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage

from django.conf import settings

from contracts.models import Contract


# @shared_task
def file_creator(context, number):
    try:
        doc = DocxTemplate(settings.MEDIA_ROOT + f'/Shablonlar/Colocation_shablon_{context["u_type"]}.docx')
        context['page_break'] = '\f'
        if context['qr_unicon']:
            path_media1 = str(context['qr_unicon']).split('/')
            path_file1 = f"/usr/src/app/{path_media1[-3]}/{path_media1[-2]}/{path_media1[-1]}"
            image1 = InlineImage(doc, path_file1, width=Mm(30))
            context['qr_unicon'] = image1
        if context['qr_client']:
            path_media2 = str(context['qr_client']).split('/')
            path_file2 = f"/usr/src/app/{path_media2[-3]}/{path_media2[-2]}/{path_media2[-1]}"
            image2 = InlineImage(doc, path_file2, width=Mm(30))
            context['qr_client'] = image2
        doc.render(context)
        if number:
            file_name = f'{context["contract_number"]}_for_preview.docx'
        else:
            file_name = f'{context["contract_number"]}_for_save.docx'

        path = settings.MEDIA_ROOT + '/Contract/' + file_name
        doc.save(path)
    except Exception as e:
        return e
    return file_name


# @shared_task
def file_downloader(base64file, pk):
    decoded_file = base64.b64decode(base64file)
    file_docx = open(f'/usr/src/app/media/Contract/DM-{pk}.docx', 'wb')
    file_docx.write(decoded_file)
    file_docx.close()
    return f'DM-{pk}.docx'


# @shared_task
# def generate_contract_number(contract_date, prefix):
#     year = contract_date.strftime("%y")
#     month = contract_date.strftime("%m")
#     day = contract_date.strftime("%d")

#     latest_contract = Contract.objects.filter(
#         id_code__startswith=f"{prefix}{year}{month}{day}"
#     ).order_by("-id").first()

#     if latest_contract:
#         counter = int(latest_contract.contract_number.split("-")[-1]) + 1
#     else:
#         counter = 1

#     contract_number = f"{prefix}{year}{month}{day}{str(counter).zfill(3)}"

#     return contract_number


@shared_task
def generate_contract_number(contract_date, prefix, obj_pk):

    year = contract_date.strftime("%y")
    month = contract_date.strftime("%m")
    day = contract_date.strftime("%d")

    latest_contract = Contract.objects.filter(
        id_code__startswith=f"{prefix}{year}{month}{day}"
    ).order_by("-id").first()

    counter = 1
    if latest_contract:
        counter = int(latest_contract.contract_number.split("-")[-1]) + 1
        
    contract_id_code = f"{prefix}{year}{month}{day}{str(counter).zfill(3)}"
    
    contract_obj = Contract.objects.get(id=obj_pk)
    contract_obj.id_code = contract_id_code
    contract_obj.save()
    return f"Updated {contract_obj.contract_number} contract's id_code"
