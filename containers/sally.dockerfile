# syntax=docker/dockerfile:1
FROM gleif/keri:1.2.16@sha256:00cb71627b2cb5999d09b2934bd28b3fc762149ae9678fab38698fba7418cd06
LABEL maintainer="GLEIF"
ENV PYTHONUNBUFFERED=1
COPY ./ /sally
WORKDIR /sally
RUN pip install . && pip check
