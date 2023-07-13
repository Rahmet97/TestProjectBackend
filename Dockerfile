FROM python:3.9.6-alpine as builder
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app

# Install system dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev \
    && apk add redis \
    && apk add libreoffice \
    && apk add --no-cache freetype-dev jpeg-dev zlib-dev \
    && apk add --no-cache libffi-dev \
    && apk add --no-cache libxml2-dev libxslt-dev \
    && apk add --no-cache cairo-dev pango-dev gdk-pixbuf-dev \

RUN apk add --no-cache \
    build-base \
    openssl-dev \
    libxml2 \
    libxslt \
    gettext \
    ttf-dejavu \
    ttf-droid \
    ttf-freefont \
    ttf-liberation \
    ttf-ubuntu-font-family

# Install WeasyPrint dependencies
RUN apk add --no-cache --virtual .build-deps \
    g++ make cairo-dev cairo pango-dev pango gdk-pixbuf-dev fontconfig \
    && apk add font-noto terminus-font \
    && fc-cache -f \
    && fc-list | sort \

# Set the default locale to support Cyrillic and Latin
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./static .
RUN rm -r /media
COPY ./media .
COPY . .