from celery import shared_task
from docxtpl import DocxTemplate

from django.conf import settings


# @shared_task
def file_creator(context):
    try:
        doc = DocxTemplate(settings.MEDIA_ROOT + f'/Shablonlar/Colocation_shablon_{context["u_type"]}.docx')
        doc.render(context)
        file_name = f'{context["contract_number"]}.docx'
        path = settings.MEDIA_ROOT + '/Contract/' + file_name
        doc.save(path)
    except Exception as e:
        return e
    return file_name
