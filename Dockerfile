FROM python:3.6
MAINTAINER Austin Riba <ariba@lco.global>

EXPOSE 8000
WORKDIR /valhalla
CMD python /valhalla/manage.py runserver 0.0.0.0:8000

RUN apt-get update && apt-get install -y gfortran

COPY docker/local_requirements.txt /valhalla
COPY requirements.txt /valhalla
RUN pip install numpy && pip install -r /valhalla/requirements.txt -r /valhalla/local_requirements.txt

# Change this per deployment
# COPY docker/prod_local_settings.py /valhalla/local_settings.py
COPY docker/test_local_settings.py /valhalla/local_settings.py

COPY . /valhalla
