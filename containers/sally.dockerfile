# syntax=docker/dockerfile:1
FROM gleif/keri:0.6.8
MAINTAINER "GLEIF"

WORKDIR /keripy
RUN pip install -e .

COPY ./ /sally

WORKDIR /sally
RUN pip install -r requirements.txt
