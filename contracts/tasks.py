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
    # os.chdir('/usr/src/app/media/Contract')
    # file_pdf = subprocess.check_output(
    #     args=['libreoffice', '--convert-to', 'pdf', f'DM-{pk}.docx']
    # )
    # print(file_pdf)
    # os.remove(f'/usr/src/app/media/Contract/DM-{pk}.docx')
    return f'DM-{pk}.docx'
