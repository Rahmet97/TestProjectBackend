import math

from rest_framework import validators, status
from .models import Tarif, ConnetMethod, UserContractTarifDevice


def error_response_404():
    raise validators.ValidationError(
        detail={"message": "Object is not found 404"}, code=status.HTTP_404_NOT_FOUND)
