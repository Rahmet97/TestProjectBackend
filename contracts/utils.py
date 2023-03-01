import os
import qrcode
import subprocess

from django.conf import settings
from rest_framework import validators, status


def error_response_404():
    raise validators.ValidationError(
        detail={"message": "Object is not found 404"}, code=status.HTTP_404_NOT_FOUND)


# Numbers to word
class NumbersToWord:

    # Digit Numbers to word: 21 -> yigirma bir
    def _hundreds(self, m):
        digits = {
            1: "bir", 2: "ikki", 3: "uch", 4: "to'rt", 5: "besh", 6: "olti", 7: "yetti", 8: "sakkiz", 9: "to'qqiz",
            10: "o'n", 20: "yigirma", 30: "o'ttiz", 40: "qirq", 50: "ellik", 60: "oltmish", 70: "yetmish", 80: "sakson",
            90: "to'qson"
        }

        d1 = m // 100
        d2 = (m // 10) % 10
        d3 = m % 10
        s1, s2, s3 = '', '', ''
        if d1 != 0:
            s1 = f'{digits[d1]} yuz '
        if d2 != 0:
            s2 = digits[d2 * 10] + ' '
        if d3 != 0:
            s3 = digits[d3] + ' '

        return s1 + s2 + s3

    # Numbers to word
    def _number2word(self, n):
        d1 = {0: "", 1: "ming ", 2: "million ", 3: "milliard ", 4: "trillion "}

        fraction = []
        while n > 0:
            r = n % 1000
            fraction.append(r)
            n //= 1000

        s = ''
        for i in range(len(fraction)):
            if fraction[i] != 0:
                yuz = self._hundreds(fraction[i]) + d1[i]
                s = yuz + s

        return s.rstrip()
    
    # change number to word
    def change_num_to_word(self, n: int) -> str:
        return self._number2word(n=n) 


# create qr code
def create_qr(link):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    file_name = link.split('/')[-1]
    file_path = f"{settings.MEDIA_ROOT}/qr/"
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    img.save(file_path + file_name.split('.')[0] + '_' + '.png')
    return file_path + file_name.split('.')[0] + '_' + '.png'


def convert_docx_to_pdf(docx_file_path: str):
    """
    docx_file_path: str -> docx file path
    -------
    return:
        pdf file path
    """
    path = "/".join(docx_file_path.split('/')[0:-1]) + '/'
    pdf_file_path = f"{path}{docx_file_path.split('/')[-1].split('.')[0]}.pdf"

    # Create the command to convert DOCX to PDF using libreoffice
    # command = ['libreoffice', '--headless', '--convert-to', 'pdf', docx_file_path, '--outdir', path]
    command = ['libreoffice', '--headless', '--convert-to', 'pdf:writer_pdf_Export:UTF8', docx_file_path, '--outdir', path]
    
    # Run the command in the terminal using subprocess with utf-8 encoding
    subprocess.call(command, encoding='utf-8')

    # subprocess.call(command)
    print("pdf", pdf_file_path)
    return pdf_file_path


def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
        print("The file has been deleted.")
    else:
        print("The file does not exist.")
