FROM python:3.9.6-alpine as builder
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev \
    && apk add redis \
    && apk add libreoffice && apk add openjdk8

COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY ./static .
RUN rm -r /media
COPY ./media .
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh
COPY . .
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]