# syntax=docker/dockerfile:1
ARG KERI_IMAGE=gleif/keri:1.2.19@sha256:a46ecb85e6210f8340465d7423195cad2a550cdff83e0dfdfa50b07062bc5e76
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
