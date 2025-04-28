# syntax=docker/dockerfile:1
FROM weboftrust/keri:1.2.7-rc1
LABEL maintainer="GLEIF"

# Disable output bufferering any output
ENV PYTHONUNBUFFERED=1

WORKDIR /keripy
RUN pip install -e .

COPY ./ /sally

WORKDIR /sally
RUN pip install -r requirements.txt
