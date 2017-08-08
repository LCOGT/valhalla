FROM python:3.6
MAINTAINER Austin Riba <ariba@lco.global>

EXPOSE 80
ENV NODE_ENV production
WORKDIR /valhalla
CMD uwsgi --ini /etc/uwsgi.ini

# todo: Revert this entire block when libcairo2 >= 1.14.2 is available from the debian jessie repo.
RUN echo 'APT::Default-Release "jessie";' > /etc/apt/apt.conf
RUN mv /etc/apt/sources.list /etc/apt/sources.list.d/jessie.list
RUN echo "deb http://ftp.debian.org/debian stretch main" > /etc/apt/sources.list.d/stretch.list

RUN curl -sL https://deb.nodesource.com/setup_7.x | bash -
RUN apt-get install -y gfortran nodejs && apt-get -t stretch install -y libcairo2=1.14.8-1

COPY requirements.txt .
RUN pip install numpy && pip install uwsgi -r requirements.txt

COPY package.json .
RUN npm install

COPY docker/uwsgi.ini /etc/

COPY . /valhalla
RUN npm run build

RUN python manage.py collectstatic --noinput
