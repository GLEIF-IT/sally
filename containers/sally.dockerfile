# syntax=docker/dockerfile:1
FROM gleif/base:0.1.0
MAINTAINER "GLEIF"

WORKDIR /usr/local/var/
RUN git clone -b development https://github.com/WebOfTrust/keripy

WORKDIR /usr/local/var/keripy
RUN pip install -r requirements.txt
RUN pip install -e .

WORKDIR /usr/local/var/keripy

WORKDIR /usr/local/var/
RUN git clone -b dev https://github.com/GLEIF-IT/sally

WORKDIR /usr/local/var/sally
RUN pip install -r requirements.txt