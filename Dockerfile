FROM python:3.6-stretch
MAINTAINER Austin Riba <ariba@lco.global>

EXPOSE 80
ENV NODE_ENV production
WORKDIR /valhalla
CMD uwsgi --ini /etc/uwsgi.ini

RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get install -y gfortran nodejs

COPY requirements.txt .
RUN pip install numpy && pip install uwsgi -r requirements.txt

COPY package.json .
RUN npm install
RUN npm install --only=dev

COPY docker/uwsgi.ini /etc/

COPY . /valhalla
RUN npm run build

RUN python manage.py collectstatic --noinput
