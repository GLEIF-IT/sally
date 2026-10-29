# Optional Sentry reporting

Install `pip install '.[sentry]'` and set `SENTRY_DSN` for the usual Sally CLI command. Without a DSN, Sally never imports the SDK. The base dependency set is unchanged; requesting Sentry without installing the extra produces an actionable startup error.

```text
SENTRY_DSN=<project DSN>
SENTRY_ENVIRONMENT=<deployment environment>
SENTRY_RELEASE=<deployed version or revision>
SALLY_SENTRY_LOG_LEVEL=INFO
```

The SDK reads the standard `SENTRY_ENVIRONMENT` and `SENTRY_RELEASE` variables. `SALLY_SENTRY_LOG_LEVEL` independently enables searchable Sentry Logs: DEBUG, INFO, WARNING, ERROR, or CRITICAL. Leave it unset to disable that separate log stream. Python's configured logger level still applies.

For a deployment image with the optional dependency:

```sh
docker build -f containers/sally.dockerfile \
  --build-arg SALLY_EXTRAS=sentry -t sally-local:sentry .
```

## What is reported

- Exceptions reaching the CLI are captured before the existing failure return, then reporting is closed and flushed.
- Caught exceptions use `logger.exception` to retain the original traceback.
- Webhook rejection and terminal drop each produce one ordinary ERROR record after Sally makes its existing queue decision. A terminal drop does not also emit a rejection report. Retries can produce further events for subsequent failed attempts.
- Unknown-credential revocations produce their existing ERROR record. Upstream's skip behavior is preserved; reporting does not restore the old crash.
- Falcon's integration captures HTTP 500 exceptions.
- Emitted DEBUG-and-higher logging records become breadcrumbs, using the SDK's normal rolling limit of 100. This is independent of searchable log forwarding.

There is no Sentry call in credential or webhook processing. `src/sally/app/reporting.py` owns optional CLI setup, capture of terminal exceptions, and shutdown. Only Falcon and Python logging integrations are enabled. Standard SDK event data, exception messages, source snippets, extras, and trace metadata are retained; there is no custom scrubber. A shared process trace is not a per-credential audit trail.

Frame-local collection is disabled because a controlled failure in the real startup path demonstrated passcode and salt arguments in SDK-default frame locals. Existing Sally INFO messages include complete webhook payloads, which can therefore appear in breadcrumbs and searchable logs. This includes personal fields in role credentials. Unwanted application log content should be corrected where Sally emits it.

## Why the HTTP adapter is required

Pinned Hio supplies a socket-address tuple for WSGI's `REMOTE_ADDR`. The [WSGI contract](https://peps.python.org/pep-3333/#environ-variables) requires a string, and Sentry's middleware calls string methods on it. Without normalization, enabling Sentry causes otherwise healthy HTTP requests to close without a response.

`src/sally/core/httping.py` provides a small `WsgiServer` subclass whose only override puts the peer IP string into that environment field. It changes request metadata, not credential verification or webhook payloads. The regression test exercises Hio's actual environment builder and response writer for HTTP 200 and HTTP 500.

## Verification

Run from the repository root:

```sh
docker build -f containers/sally-test.dockerfile -t sally-test:base .
docker build -f containers/sally-test.dockerfile \
  --build-arg SALLY_EXTRAS=test,sentry -t sally-test:enabled .
docker run --rm --network none sally-test:base
docker run --rm --network none sally-test:enabled
```

`tests/app/test_reporting.py` checks the optional dependency boundary, breadcrumbs, source context, log thresholds, trace correlation, startup frame-local exclusion, CLI failure, and actual Hio HTTP responses.

`tests/integration/check_reporting.py` runs ten scenarios with real disposable credential stores, scheduler, and signed webhook client. Run it in the test image with `python tests/integration/check_reporting.py --output /tmp/reporting`; add `--sentry`, then optionally `--logs-level WARNING` or `--logs-level INFO`. CI runs all four modes. Results include final queue states, webhook body hashes, actual SDK envelopes, and observed data categories. The receiver is loopback-only; no hosted Sentry, witness network, or production database participates.

## Operational limits

The SDK adds process-wide logging/Falcon patches, serialization, an asynchronous sender, and a bounded shutdown flush. Setup is owned by a CLI process; embedding Sally alongside an existing Sentry client is outside this MVP. SDK queues are not durable and repeated failed attempts can consume ingestion volume.

Reporting observes failures; it does not change retry/drop decisions or repair silent stalls, absent input, startup queue clearing, or downstream failures after HTTP acceptance. Queue/progress metrics and end-to-end checks address those cases.
