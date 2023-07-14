FROM python:3.9.6-alpine as builder
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app

# Install system dependencies
RUN apk update && apk add --no-cache \
    postgresql-dev gcc python3-dev musl-dev \
    redis \
    libreoffice \
    freetype-dev jpeg-dev zlib-dev \
    libffi-dev \
    libxml2-dev libxslt-dev \
    cairo-dev pango-dev gdk-pixbuf-dev \
    build-base openssl-dev libxml2 libxslt gettext \
    ttf-dejavu  # or replace with the alternative font package

# Install WeasyPrint dependencies
RUN apk add --no-cache --virtual .build-deps \
    g++ make cairo-dev cairo pango-dev pango gdk-pixbuf-dev fontconfig \
    font-noto terminus-font \
    && fc-cache -f \
    && fc-list | sort

# Set the default locale to support Cyrillic and Latin
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./static .
RUN rm -r /media
COPY ./media .
COPY . .
