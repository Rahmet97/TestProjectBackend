from rest_framework import validators


def responseErrorMessage(message, status_code):
    raise validators.ValidationError(
        detail={"message": f"{message}"}, code=status_code)

