# syntax=docker/dockerfile:1
FROM weboftrust/keri:1.1.8
MAINTAINER "GLEIF"

# Disable output bufferering any output
ENV PYTHONUNBUFFERED=1

WORKDIR /keripy
RUN pip install -e .

COPY ./ /sally

WORKDIR /sally
RUN pip install -r requirements.txt
