from celery import shared_task
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage

from django.conf import settings


# @shared_task
def file_creator(context):
    try:
        doc = DocxTemplate(settings.MEDIA_ROOT + f'/Shablonlar/Colocation_shablon_{context["u_type"]}.docx')
        if context['qr_unicon']:
            path_media1 = str(context['qr_unicon']).split('/')
            path_file1 = f"/usr/src/app/{path_media1[-3]}/{path_media1[-2]}/{path_media1[-1]}"
            print(path_file1)
            image1 = InlineImage(doc, path_file1, width=Mm(50))
            context['qr_unicon'] = image1
        if context['qr_client']:
            path_media2 = str(context['qr_client']).split('/')
            path_file2 = f"/usr/src/app/{path_media2[-3]}/{path_media2[-2]}/{path_media2[-1]}"
            print(path_file2)
            image2 = InlineImage(doc, path_file2, width=Mm(50))
            context['qr_client'] = image2
        doc.render(context)
        file_name = f'{context["contract_number"]}.docx'
        path = settings.MEDIA_ROOT + '/Contract/' + file_name
        doc.save(path)
    except Exception as e:
        return e
    return file_name
