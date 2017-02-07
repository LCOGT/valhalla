FROM python:3.6
MAINTAINER Austin Riba <ariba@lco.global>

EXPOSE 8000
ENV NODE_ENV production
WORKDIR /valhalla
CMD python manage.py runserver 0.0.0.0:8000

RUN curl -sL https://deb.nodesource.com/setup_7.x | bash -
RUN apt-get install -y gfortran nodejs

COPY docker/local_requirements.txt .
COPY requirements.txt .
RUN pip install numpy && pip install -r requirements.txt -r local_requirements.txt

COPY package.json .
RUN npm install

# Change this per deployment
# COPY docker/prod_local_settings.py /valhalla/local_settings.py
COPY docker/test_local_settings.py local_settings.py

COPY . /valhalla
RUN npm run build
