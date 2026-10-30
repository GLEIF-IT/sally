# Optional Sentry reporting

Install `pip install '.[sentry]'` and set `SENTRY_DSN` for the usual Sally CLI command. Without a DSN, Sally never imports the SDK. The base dependency set is unchanged; requesting Sentry without installing the extra produces an actionable startup error.

```text
SENTRY_DSN=<project DSN>
SENTRY_ENVIRONMENT=<deployment environment>
SENTRY_RELEASE=<deployed version or revision>
SALLY_SENTRY_LOG_LEVEL=INFO
```

The SDK reads the standard `SENTRY_ENVIRONMENT` and `SENTRY_RELEASE` variables. `SALLY_SENTRY_LOG_LEVEL` independently enables searchable Sentry Logs: DEBUG, INFO, WARNING, ERROR, or CRITICAL. Leave it unset to disable that separate log stream. Python's configured logger level still applies.

### Optional HTTP tracing

Set `SENTRY_TRACES_SAMPLE_RATE=0.1` to sample 10% of incoming Falcon HTTP requests, or `1.0` to capture every request in a local demonstration. Leave it unset to disable tracing entirely. Values must be numbers between 0 and 1; invalid configuration fails at startup. A value of `0` samples no new root transactions but can still honor an incoming sampling decision. This option requires the same SDK extra and DSN as error reporting.

The existing Falcon integration supplies request durations, route names, response status, and correlation with HTTP errors. No decorators, additional dependency, or Sentry call is added to credential processing. Health requests are included in the configured sample. This is request tracing, not an end-to-end credential trace: KERI escrows, Hio's outbound webhook client, and LMDB operations are not automatically instrumented by these integrations. Background work after HTTP acceptance does not inherit the request's trace. Following one credential across retries would require explicit per-credential context and spans with lifetimes matching that work, rather than a transaction around the long-running scheduler.

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

### Expected exceptions and noise

Hio uses `StopIteration` and `GeneratorExit` for task completion and cancellation. KERIpy uses exceptions such as `MissingRegistryError`, `MissingSchemaError`, and `MissingWitnessSignatureError` to retain work in escrow until dependencies arrive. A caught exception alone is not reported by this setup: it must escape to the CLI, produce an HTTP 5xx, or be explicitly captured through ERROR logging. Falcon's ordinary HTTP 4xx exceptions do not become error events.

There is a concrete exception to the quiet-retry behavior in pinned KERIpy: some expected escrow handlers call `logger.exception` when their logger is enabled for `TRACE`. Those ERROR records become Sentry issues even though the credential remains pending normally. The regression test exercises a real missing-registry escrow twice: INFO and DEBUG produce no reports; TRACE produces two. KERIpy's `TRACE` log level is unrelated to enabling Sentry tracing. Keep the normal application log level unless investigating that library in detail; no exception classes or breadcrumbs are blanket-filtered here.

Sally's own rejected presentations and unknown-credential messages are deliberately reported through their existing ERROR records. These can be useful operational signals without indicating a software crash. A terminal failure and an expected wait can share the `ValidationError` hierarchy, so ignoring that base class would hide real failures too.

## Why the HTTP adapter is required

Pinned Hio supplies a socket-address tuple for WSGI's `REMOTE_ADDR`. The [WSGI contract](https://peps.python.org/pep-3333/#environ-variables) requires a string, and Sentry's middleware calls string methods on it. Without normalization, enabling Sentry causes otherwise healthy HTTP requests to close without a response.

`src/sally/core/httping.py` provides a small `WsgiServer` subclass whose only override puts the peer IP string into that environment field. It changes request metadata, not credential verification or webhook payloads. The regression test exercises Hio's actual environment builder and response writer for HTTP 200 and HTTP 500.

`tests/core/test_httping.py` additionally compares the adapter's environment with pinned Hio's own builder: every other field, including method, path, query, signature headers, body bytes, and WSGI flags, must match. It covers IPv4/IPv6 address values with and without `X-Forwarded-For`, and checks that the transport retains its original `(IP, port)` address. The intentional observable change is that Falcon's `remote_addr` and the peer entry in `access_route` contain the IP string. Custom middleware depending on Hio's old tuple would observe that correction too.

## Verification

Run from the repository root:

```sh
docker build -f containers/sally-test.dockerfile -t sally-test:base .
docker build -f containers/sally-test.dockerfile \
  --build-arg SALLY_EXTRAS=test,sentry -t sally-test:enabled .
docker run --rm --network none sally-test:base
docker run --rm --network none sally-test:enabled
```

`tests/app/test_reporting.py` checks the optional dependency boundary, breadcrumbs, source context, log thresholds, trace correlation, startup frame-local exclusion, CLI failure, expected Hio/KERIpy exceptions, and actual Hio HTTP 200/400/500 responses with tracing disabled, zero-sampled, and enabled.

`tests/integration/check_reporting.py` runs ten scenarios with real disposable credential stores, scheduler, and signed webhook client. Run it in the test image with `python tests/integration/check_reporting.py --output /tmp/reporting`; add `--sentry`, then optionally `--logs-level WARNING` or `--logs-level INFO`. CI runs all four modes. Results include final queue states, webhook body hashes, actual SDK envelopes, and observed data categories. The receiver is loopback-only; no hosted Sentry, witness network, or production database participates.

## Operational limits

The SDK adds process-wide logging/Falcon patches, serialization, an asynchronous sender, and a bounded shutdown flush. Setup is owned by a CLI process; embedding Sally alongside an existing Sentry client is outside this MVP. SDK queues are not durable and repeated failed attempts can consume ingestion volume.

Reporting observes failures; it does not change retry/drop decisions or repair silent stalls, absent input, startup queue clearing, or downstream failures after HTTP acceptance. Queue/progress metrics and end-to-end checks address those cases.
