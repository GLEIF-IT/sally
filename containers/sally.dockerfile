# syntax=docker/dockerfile:1
FROM gleif/keri:1.2.15@sha256:b4dcb636d224465dd186463d8b4c37a453ae343c374eb1a069a7e011189723bd
LABEL maintainer="GLEIF"
ENV PYTHONUNBUFFERED=1
COPY ./ /sally
WORKDIR /sally
RUN pip install . && pip check
