# syntax=docker/dockerfile:1
FROM gleif/keri:0.6.7
MAINTAINER "GLEIF"

WORKDIR /
RUN git clone https://github.com/ioflo/hio.git
WORKDIR /hio
RUN pip install -e .


WORKDIR /keripy
RUN pip install -e .

COPY ./ /sally

WORKDIR /sally
RUN pip install -r requirements.txt
