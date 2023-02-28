import os
import math
import subprocess

from django.http.response import HttpResponse

from rest_framework import validators, status
from .models import Tarif, ConnetMethod, UserContractTarifDevice


def error_response_404():
    raise validators.ValidationError(
        detail={"message": "Object is not found 404"}, code=status.HTTP_404_NOT_FOUND)


def convert_docx_to_pdf(docx_file_path: str):
    """
    docx_file_path: str -> docx file path
    -------
    return:
        pdf file path
    """
    
    path = "/".join(docx_file_path.split('.')[0].split('/')[:-1])
    pdf_file_path = f"{path}_pdf"

    # Create the command to convert DOCX to PDF using libreoffice
    command = ['libreoffice', '--headless', '--convert-to', 'pdf', docx_file_path, '--outdir', pdf_file_path]
    # Run the command in the terminal using subprocess
    subprocess.run(command)
    
    return f"{pdf_file_path}/{docx_file_path.split('/')[-1].split('.')[0]}.pdf"


def delete_pdf_file(pdf_file_path: str):
    if os.path.exists(pdf_file_path):
        os.remove(pdf_file_path)
        print(f"The file has been deleted.")
    else:
        print(f"The file does not exist.")
