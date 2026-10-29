# syntax=docker/dockerfile:1
FROM gleif/keri:1.2.17@sha256:a0828c0f056a4abedfb9b475e95fe35fd16fceee2afb7f5f8dffc87a0a776ff2
LABEL maintainer="GLEIF"
ENV PYTHONUNBUFFERED=1
COPY ./ /sally
WORKDIR /sally
ARG SALLY_EXTRAS
RUN pip install ".${SALLY_EXTRAS:+[$SALLY_EXTRAS]}" && pip check
