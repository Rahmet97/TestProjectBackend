FROM python:3.9.6-alpine as builder
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app

#RUN apk update \
#    && apk add postgresql-dev gcc python3-dev musl-dev \
#    && apk add redis \
#    && apk add libreoffice \
#    && apk add --no-cache freetype-dev jpeg-dev zlib-dev \
#    && apk add --no-cache libffi-dev \

# Install system dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev \
    && apk add redis \
    && apk add libreoffice \
    && apk add --no-cache freetype-dev jpeg-dev zlib-dev \
    && apk add --no-cache libffi-dev \
    && apk add --no-cache libxml2-dev libxslt-dev \
    && apk add --no-cache cairo-dev pango-dev gdk-pixbuf-dev

# Install WeasyPrint dependencies
RUN apk add --no-cache --virtual .build-deps \
    g++ make cairo-dev cairo pango-dev pango gdk-pixbuf-dev fontconfig

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./static .
RUN rm -r /media
COPY ./media .
#COPY ./entrypoint.sh .
#RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
#RUN chmod +x /usr/src/app/entrypoint.sh
COPY . .
#ENTRYPOINT ["/usr/src/app/entrypoint.sh"]