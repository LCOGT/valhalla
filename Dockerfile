FROM python:3.6-stretch
MAINTAINER Austin Riba <ariba@lco.global>

EXPOSE 80
ENV NODE_ENV production
ENV STATIC_STORAGE whitenoise.storage.CompressedManifestStaticFilesStorage
WORKDIR /valhalla
CMD gunicorn valhalla.wsgi -w 4 -k gevent -b 0.0.0.0:80

RUN curl -sL https://deb.nodesource.com/setup_9.x | bash -
RUN apt-get install -y gfortran nodejs

COPY requirements.txt .
RUN pip install numpy && pip install -r requirements.txt

COPY package.json package-lock.json ./
RUN npm install && npm install --only=dev

COPY . /valhalla
RUN npm run build

RUN python manage.py collectstatic --noinput
