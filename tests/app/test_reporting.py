"""The optional boundary must hold both with and without the SDK installed."""
import importlib.util
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import falcon
from falcon import testing
import pytest

from sally.app import reporting
from sally.app.cli import kli


def test_unconfigured_process_never_imports_sdk():
    env = dict(os.environ)
    env.pop("SENTRY_DSN", None)
    env["SALLY_SENTRY_LOG_LEVEL"] = "INFO"
    env["SENTRY_TRACES_SAMPLE_RATE"] = "1.0"
    subprocess.run([sys.executable, "-c", """
import sys, threading
from sally.app import reporting
from sally.app.cli import kli
before = threading.active_count()
with reporting.session():
    pass
assert not any(name.startswith('sentry_sdk') for name in sys.modules)
assert threading.active_count() == before
"""], env=env, check=True)


def test_configured_without_extra_fails_clearly(monkeypatch):
    if importlib.util.find_spec("sentry_sdk"):
        pytest.skip("Exercises the base install, which has no SDK")
    monkeypatch.setenv("SENTRY_DSN", "http://public@127.0.0.1:9/1")
    with pytest.raises(RuntimeError, match=r"requires sally\[sentry\]"):
        with reporting.session():
            pytest.fail("Must fail before executing application work")


@pytest.fixture
def transport_events(monkeypatch):
    sdk = pytest.importorskip("sentry_sdk")
    from sentry_sdk.transport import Transport

    events = []
    logs = []
    transactions = []

    class MemoryTransport(Transport):
        def capture_envelope(self, envelope):
            events.extend(item.payload.json for item in envelope.items if item.type == "event")
            transactions.extend(item.payload.json for item in envelope.items if item.type == "transaction")
            logs.extend(log for item in envelope.items if item.type == "log"
                        for log in item.payload.json["items"])

    MemoryTransport.logs = logs
    MemoryTransport.transactions = transactions
    init = sdk.init
    previous = sdk.get_global_scope().client
    monkeypatch.setattr(sdk, "init", lambda **options: init(transport=MemoryTransport, **options))

    monkeypatch.setenv("SENTRY_DSN", "http://public@127.0.0.1:9/1")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "test")
    monkeypatch.delenv("SALLY_SENTRY_LOG_LEVEL", raising=False)
    monkeypatch.delenv("SENTRY_TRACES_SAMPLE_RATE", raising=False)
    with sdk.isolation_scope() as scope:
        scope.clear()
        try:
            yield sdk, events, MemoryTransport
        finally:
            sdk.get_global_scope().set_client(previous)


@pytest.fixture
def captured(transport_events):
    sdk, events, transport = transport_events
    with reporting.session():
        yield sdk, events


def test_only_explicit_falcon_integration_and_no_tracing(captured):
    sdk, events = captured
    client = sdk.get_client()
    assert set(client.integrations) == {"falcon", "logging"}
    assert not client.options["traces_sample_rate"]
    assert client.options["include_local_variables"] is False
    assert client.options["before_send"] is None
    assert client.options["before_breadcrumb"] is None
    assert client.options["include_source_context"] is True


def test_exception_retains_message_context_extras_and_breadcrumbs(captured):
    sdk, events = captured
    detail = "fixture-credential-detail"
    sdk.set_extra("credential", detail)
    sdk.add_breadcrumb(message=detail)
    trace_id = sdk.get_current_scope().get_trace_context()["trace_id"]
    try:
        raise ValueError(detail)
    except ValueError as error:
        sdk.capture_exception(error, tags={"component": "escrow"})
    assert len(events) == 1
    event = events[0]
    assert event["extra"]["credential"] == detail
    assert event["breadcrumbs"]["values"][-1]["message"] == detail
    assert event["contexts"]["trace"]["trace_id"] == trace_id
    error = event["exception"]["values"][-1]
    assert error["type"] == "ValueError"
    assert error["value"] == detail
    frame = error["stacktrace"]["frames"][-1]
    assert frame["function"] == "test_exception_retains_message_context_extras_and_breadcrumbs"
    assert "raise ValueError(detail)" in frame["context_line"]
    assert "vars" not in frame
    assert event["tags"] == {"component": "escrow"}


def test_cli_caught_error_still_reports_and_returns_failure(transport_events, monkeypatch):
    sdk, events, transport = transport_events

    def fail(args):
        raise AttributeError("private credential content")

    parser = SimpleNamespace(parse_args=lambda: SimpleNamespace(handler=fail))
    monkeypatch.setattr(kli.multicommand, "create_parser", lambda commands: parser)
    assert kli.main() == -1
    assert len(events) == 1
    assert events[0]["tags"] == {"component": "cli"}


def test_session_reports_rethrows_and_closes_client(transport_events):
    sdk, events, transport = transport_events
    with pytest.raises(AttributeError):
        with reporting.session():
            raise AttributeError("private credential content")
    assert len(events) == 1
    assert events[0]["tags"]["component"] == "cli"
    assert sdk.get_client().transport is None


def test_falcon_500_retains_sdk_request_context(captured):
    sdk, events = captured

    class Failure:
        def on_post(self, req, resp):
            raise ValueError(req.media["credential"])

    app = falcon.App()
    app.add_route("/credential", Failure())
    result = testing.TestClient(app).simulate_post("/credential", json={"credential": "private-body"},
                                                 headers={"X-Private": "private-header"})
    assert result.status_code == 500
    assert len(events) == 1
    raw = json.dumps(events)
    assert "private-body" in raw
    assert "private-header" in raw
    assert events[0]["request"]["method"] == "POST"
    assert events[0]["request"]["url"].endswith("/credential")


def test_ordinary_error_logs_create_issues_and_breadcrumbs(captured):
    import logging
    sdk, events = captured
    logger = logging.getLogger("sally")
    logger.warning("Revocation received", extra={"credential": "fixture-said"})
    logger.error("Unknown credential")
    assert len(events) == 1
    assert events[0]["logentry"]["formatted"] == "Unknown credential"
    breadcrumb = events[0]["breadcrumbs"]["values"][-1]
    assert breadcrumb["message"] == "Revocation received"
    assert breadcrumb["data"]["credential"] == "fixture-said"


def test_exception_logging_captures_one_error_with_original_traceback(captured):
    import logging
    sdk, events = captured
    try:
        raise ValueError("credential-content-must-remain-local")
    except ValueError:
        logging.getLogger("sally").exception("Caught failure", extra={"sally_component": "escrow"})
    assert len(events) == 1
    assert events[0]["extra"]["sally_component"] == "escrow"
    error = events[0]["exception"]["values"][-1]
    assert error["type"] == "ValueError"
    assert error["stacktrace"]["frames"][-1]["function"] == "test_exception_logging_captures_one_error_with_original_traceback"
    assert error["value"] == "credential-content-must-remain-local"
    sdk.flush()
    assert sdk.get_client().transport.logs == []


@pytest.mark.parametrize("level,expected", [
    ("WARNING", ["Retrying delivery", "unrelated-library-message", "Caught delivery failure"]),
    ("INFO", ["Below the chosen Sentry threshold", "Retrying delivery", "unrelated-library-message", "Caught delivery failure"]),
])
def test_logging_opt_in_preserves_extras_and_trace_correlation(transport_events, monkeypatch, level, expected):
    import logging
    from sally import ogler, log_name
    sdk, events, transport = transport_events
    monkeypatch.setenv("SALLY_SENTRY_LOG_LEVEL", level)
    logger = ogler.getLogger(log_name)
    with reporting.session():
        logger.info("Below the chosen Sentry threshold")
        logger.warning("Retrying delivery", extra={"credential": "private-extra"})
        logging.getLogger("unrelated-library").error("unrelated-library-message")
        try:
            raise ValueError("private-exception")
        except ValueError:
            logger.exception("Caught delivery failure", extra={"sally_component": "escrow"})
    assert len(events) == 2
    assert [log["body"] for log in transport.logs] == expected
    assert "private-extra" in json.dumps(transport.logs)
    event = events[-1]
    assert event["exception"]["values"][-1]["type"] == "ValueError"
    assert event["exception"]["values"][-1]["value"] == "private-exception"
    assert event["contexts"]["trace"]["trace_id"] == transport.logs[-1]["trace_id"]
    assert "Below the chosen Sentry threshold" in [b["message"] for b in event["breadcrumbs"]["values"]]


def test_invalid_sentry_log_level_fails_before_application_work(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "http://public@127.0.0.1:9/1")
    monkeypatch.setenv("SALLY_SENTRY_LOG_LEVEL", "LOUD")
    with pytest.raises(ValueError, match="got 'LOUD'"):
        with reporting.session():
            pytest.fail("Invalid configuration must not run the application")


@pytest.mark.parametrize("rate", ["loud", "", "-0.1", "1.1", "nan", "inf"])
def test_invalid_trace_rate_fails_before_application_work(monkeypatch, rate):
    monkeypatch.setenv("SENTRY_DSN", "http://public@127.0.0.1:9/1")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", rate)
    with pytest.raises(ValueError, match="SENTRY_TRACES_SAMPLE_RATE expects"):
        with reporting.session():
            pytest.fail("Invalid configuration must not run the application")


@pytest.mark.parametrize("level,expected_reports", [("INFO", 0), ("DEBUG", 0), ("TRACE", 2)])
def test_keripy_expected_registry_retries_only_report_when_trace_logging_emits_errors(captured, request, level, expected_reports):
    import logging
    from keri import kering
    from keri.app import habbing
    from keri.core import coring
    from keri.vc import proving
    from keri.vdr import verifying, viring

    sdk, events = captured
    original_level = verifying.logger.level
    verifying.logger.setLevel(getattr(logging, level))
    request.addfinalizer(lambda: verifying.logger.setLevel(original_level))
    with habbing.openHab(name="expected-retry", temp=True) as (hby, hab), \
            viring.openReger(name="expected-retry", temp=True) as reger:
        verifier = verifying.Verifier(hby=hby, reger=reger)
        digest = coring.Diger(ser=b"test-only-missing-registry").qb64
        creder = proving.credential(schema=digest, issuer=hab.pre, data={}, status=digest)
        with pytest.raises(kering.MissingRegistryError):
            verifier.processCredential(creder, coring.Prefixer(qb64=hab.pre),
                                       coring.Seqner(sn=0), coring.Saider(qb64=digest))
        assert events == []
        for _ in range(2):
            verifier.processEscrows()
            assert reger.mre.get(keys=(creder.said,)) is not None
        assert len(events) == expected_reports
        assert all(event["exception"]["values"][-1]["type"] == "MissingRegistryError" for event in events)


def test_hio_task_completion_and_cancellation_do_not_report(captured):
    from hio.base import doing

    sdk, events = captured
    completed = []
    cancelled = []

    def finish(tymth, tock=0.0, **opts):
        yield tock
        completed.append(True)
        return True

    def wait(tymth, tock=0.0, **opts):
        try:
            while True:
                yield tock
        finally:
            cancelled.append(True)

    doing.Doist(limit=0.1).do(doers=[doing.doify(finish), doing.doify(wait)])
    assert completed == [True]
    assert cancelled == [True]
    assert events == []


def test_startup_failure_excludes_passcode_and_salt(transport_events, monkeypatch):
    from sally.app.cli.commands.server import start
    sdk, events, transport = transport_events
    args = start.parser.parse_args([
        "--alias", "audit", "--web-hook", "http://127.0.0.1:9/", "--auth", "audit",
        "--passcode", "-".join(("TEST", "ONLY", "PASSCODE", "MARKER")),
        "--salt", "-".join(("TEST", "ONLY", "SALT", "MARKER")),
    ])

    def fail_before_keystore(**kwargs):
        raise RuntimeError("Synthetic startup failure before opening a keystore")

    monkeypatch.setattr(start, "init_habery", fail_before_keystore)
    monkeypatch.setattr(kli.multicommand, "create_parser", lambda commands: SimpleNamespace(parse_args=lambda: args))
    assert kli.main() == -1
    assert len(events) == 1
    raw = json.dumps(events)
    assert args.bran not in raw
    assert args.salt not in raw
    frames = events[0]["exception"]["values"][-1]["stacktrace"]["frames"]
    assert any(frame["function"] == "launch" for frame in frames)


@pytest.mark.parametrize("trace_rate", [None, "0", "1"])
@pytest.mark.parametrize("path,status", [("/health", 200), ("/failure", 500), ("/rejected", 400)])
def test_real_hio_wsgi_response_with_sentry(transport_events, monkeypatch, path, status, trace_rate):
    from hio.core.http.serving import Responder
    from hio.help import Hict
    from sally.core import httping, monitoring
    sdk, events, transport = transport_events
    if trace_rate is not None:
        monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", trace_rate)

    class Failure:
        def on_get(self, req, resp):
            raise ValueError("Controlled HTTP failure")

    class Rejected:
        def on_get(self, req, resp):
            raise falcon.HTTPBadRequest(title="Controlled request rejection")

    with reporting.session():
        app = falcon.App()
        app.add_route("/health", monitoring.HealthEnd())
        app.add_route("/failure", Failure())
        app.add_route("/rejected", Rejected())
        server = httping.WsgiServer(app=app, port=9723)
        request = SimpleNamespace(body=b"", method="GET", path=path, query="", version=(1, 1),
                                  headers=Hict(), length=0, remoter=SimpleNamespace(ca=("127.0.0.1", 12345)))
        chunks = []
        response = Responder(incomer=SimpleNamespace(tx=chunks.append), app=app,
                             environ=server.buildEnviron(request), chunkable=True)
        for _ in range(10):
            response.service()
            if response.ended or response.closed:
                break
    assert response.ended and not response.errored, repr(response.error)
    assert b"".join(chunks).startswith(f"HTTP/1.1 {status} ".encode())
    assert len(events) == (1 if status == 500 else 0)
    assert len(transport.transactions) == (1 if trace_rate == "1" else 0)
    if trace_rate == "1":
        transaction = transport.transactions[0]
        assert transaction["contexts"]["trace"]["op"] == "http.server"
        assert transaction["transaction"] == path
        assert transaction["request"]["method"] == "GET"
        if events:
            assert events[0]["contexts"]["trace"]["trace_id"] == transaction["contexts"]["trace"]["trace_id"]
