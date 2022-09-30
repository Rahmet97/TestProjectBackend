from celery import shared_task
from docxtpl import DocxTemplate

from TestProject.settings import BASE_DIR


@shared_task
def file_creator(context):
    try:
        doc = DocxTemplate(BASE_DIR + '/media/Shablonlar/Colocation_shablon.docx')
        doc.render(context)
        doc.save(BASE_DIR + f'/media/Contract/{context["client"]}.docx')
    except Exception as e:
        return e
    return True
