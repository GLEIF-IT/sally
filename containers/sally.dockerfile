# syntax=docker/dockerfile:1
FROM gleif/keri:1.2.8-rc2
LABEL maintainer="GLEIF"

# Disable output bufferering any output
ENV PYTHONUNBUFFERED=1

WORKDIR /keripy
RUN pip install -e .

COPY ./ /sally

WORKDIR /sally
RUN pip install -r requirements.txt
