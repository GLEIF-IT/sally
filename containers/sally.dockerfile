# syntax=docker/dockerfile:1
ARG KERI_IMAGE=gleif/keri:1.2.18@sha256:dcf31bdbff69cbb5d69abbedebdcf6c203bfdbb95f5f582432b2d6359e331793
FROM ${KERI_IMAGE} AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /bin/uv
COPY ./ /sally
WORKDIR /sally
RUN uv pip install --python /keripy/venv/bin/python --no-deps . \
    && uv pip check --python /keripy/venv/bin/python

FROM ${KERI_IMAGE}
LABEL maintainer="GLEIF"
ENV PYTHONUNBUFFERED=1
COPY ./ /sally
COPY --from=builder /keripy/venv /keripy/venv
WORKDIR /sally
