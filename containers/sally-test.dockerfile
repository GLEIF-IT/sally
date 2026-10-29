FROM gleif/keri:1.2.17@sha256:a0828c0f056a4abedfb9b475e95fe35fd16fceee2afb7f5f8dffc87a0a776ff2
ARG SALLY_EXTRAS=test
WORKDIR /sally
COPY setup.py README.md LICENSE /sally/
COPY src /sally/src
COPY tests /sally/tests
RUN pip install ".[${SALLY_EXTRAS}]" && pip check
ENTRYPOINT []
CMD ["pytest", "tests", "-q"]
