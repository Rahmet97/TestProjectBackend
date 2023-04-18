FROM python:3.9.6-alpine as builder
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev \
    && apk add redis \
    && apk add libreoffice \
    && apk add --no-cache freetype-dev jpeg-dev zlib-dev \
    && apk update && apk add libffi-dev

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY ./static .
RUN rm -r /media
COPY ./media .
# COPY ./entrypoint.sh .
# RUN sed -i 's/\r$//g' /usr/src/app/TestProjectBackend/entrypoint.sh
# RUN chmod +x /usr/src/app/TestProjectBackend/entrypoint.sh
COPY . .
# ENTRYPOINT ["/usr/src/app/TestProjectBackend/entrypoint.sh"]
# CMD ["gunicorn", "TestProject.wsgi:application", "--bind", "0.0.0.0:8000"]