# -*- encoding: utf-8 -*-
"""
Tests for sally.core.metrics and the /metrics endpoint in sally.core.monitoring
"""
import falcon
import pytest
from falcon import testing
from keri.app import habbing
from keri.core import coring
from keri.db import dbing
from keri.vdr import viring

import issuing
import sally
from sally.core import basing, inspecting, metrics, monitoring
from test_inspecting import load_credential


def test_render_exposition_format():
    m = metrics.Metrics()
    m.inc("sally_webhook_responses_total", outcome="success", action="iss")
    m.inc("sally_webhook_responses_total", outcome="success", action="iss")
    m.set("sally_pipeline_depth", 3, stage='a"b\n')
    text = m.render()

    assert text.endswith("\n")
    lines = text.splitlines()
    assert lines[0] == "# HELP sally_info Sally build information. Always 1."
    assert lines[1] == "# TYPE sally_info gauge"
    assert lines[2] == f'sally_info{{version="{sally.__version__}"}} 1'
    # labels are emitted sorted by key, values escaped
    assert 'sally_pipeline_depth{stage="a\\"b\\n"} 3' in lines
    assert 'sally_webhook_responses_total{action="iss",outcome="success"} 2' in lines
    # pre-seeded zeros are present so increase() sees the first event
    assert 'sally_webhook_responses_total{action="rev",outcome="failure"} 0' in lines
    for kind in metrics.EXCEPTION_KINDS:
        assert f'sally_exceptions_total{{kind="{kind}"}} 0' in lines
    assert "# TYPE sally_exceptions_total counter" in lines
    # families are emitted once and in catalogue order
    types = [l for l in lines if l.startswith("# TYPE")]
    assert len(types) == len(set(types))
    assert types.index("# TYPE sally_info gauge") < types.index("# TYPE sally_exceptions_total counter")
    # families with no series are omitted
    assert "sally_credentials_unverified" not in text


def test_undeclared_metric_raises():
    m = metrics.Metrics()
    with pytest.raises(KeyError):
        m.inc("sally_nope_total")
    with pytest.raises(KeyError):
        m.set("sally_nope", 1)


def test_inc_get_clear():
    m = metrics.Metrics()
    assert m.get("sally_exceptions_total", kind=metrics.UNSUPPORTED_SCHEMA) == 0
    m.inc("sally_exceptions_total", kind=metrics.UNSUPPORTED_SCHEMA)
    assert m.get("sally_exceptions_total", kind=metrics.UNSUPPORTED_SCHEMA) == 1
    assert m.get("sally_credentials", type="LE", status="issued") is None
    m.set("sally_credentials", 4, type="LE", status="issued")
    m.clear("sally_credentials")
    assert m.get("sally_credentials", type="LE", status="issued") is None


def test_summarize():
    report = dict(
        identifiers=[],
        registries=[dict(), dict()],
        credentials=[
            dict(type="LE", status=inspecting.ISSUED, verified=True, missingEdges=[]),
            dict(type="LE", status=inspecting.ISSUED, verified=True, missingEdges=["EABC"]),
            dict(type="unknown", status=inspecting.ISSUED, verified=False, missingEdges=[]),
            dict(type="QVI", status=inspecting.UNKNOWN_REGISTRY, verified=False, missingEdges=[]),
        ],
        telOnly=[dict(), dict(), dict()],
        escrows=dict(telOutOfOrder=[dict(knownCredential=True), dict(knownCredential=False)]),
        pipeline=dict(),
    )
    summary = inspecting.summarize(report)
    assert summary["credentials"] == {
        ("LE", inspecting.ISSUED): 2,
        ("unknown", inspecting.ISSUED): 1,
        ("QVI", inspecting.UNKNOWN_REGISTRY): 1,
    }
    assert summary["unverified"] == 2
    assert summary["missingEdges"] == 1
    assert summary["telOnly"] == 3
    assert summary["telOutOfOrderUnknown"] == 1
    assert summary["registries"] == 2


def make_client(m, hby, reger, cdb, **kwa):
    app = falcon.App()
    app.add_route("/metrics", monitoring.MetricsEnd(metrics=m, db=hby.db, reger=reger, cdb=cdb, **kwa))
    return testing.TestClient(app)


def test_metrics_endpoint_cheap_gauges():
    with habbing.openHab(name="test", base="test", temp=True) as (hby, hab):
        cdb = basing.CueBaser(name="test_cb", temp=True)
        reger = viring.Reger(name="test", db=hby.db, temp=True)
        m = metrics.Metrics()
        client = make_client(m, hby, reger, cdb)

        result = client.simulate_get("/metrics")
        assert result.status == falcon.HTTP_OK
        assert result.headers["content-type"] == metrics.CONTENT_TYPE
        lines = result.text.splitlines()
        assert f'sally_info{{version="{sally.__version__}"}} 1' in lines
        assert 'sally_pipeline_depth{stage="iss"} 0' in lines
        assert "sally_credentials_stored 0" in lines
        assert "sally_registries 0" in lines
        assert 'sally_acdc_escrow{reason="missing_schema"} 0' in lines
        assert 'sally_tel_escrow{reason="anchorless"} 0' in lines
        # an empty store still reports every type/status combination so dashboards see zeros
        assert 'sally_credentials{status="unknown-registry",type="unknown"} 0' in lines
        assert "sally_tel_only_credentials 0" in lines

        said = "EElymNmgs1u0mSaoCeOtSsNOROLuqOz103V3-4E-ClXH"
        cdb.snd.pin(keys=(said,), val=coring.Prefixer(qb64=hab.pre))
        cdb.iss.pin(keys=(said,), val=coring.Dater())
        m.inc("sally_exceptions_total", kind=metrics.REVOCATION_UNKNOWN_CREDENTIAL)

        lines = client.simulate_get("/metrics").text.splitlines()
        assert 'sally_pipeline_depth{stage="iss"} 1' in lines
        assert "sally_known_senders 1" in lines
        assert 'sally_exceptions_total{kind="revocation_unknown_credential"} 1' in lines


def test_metrics_endpoint_snapshot_cache(monkeypatch):
    calls = []
    real = inspecting.collect

    def counting(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(inspecting, "collect", counting)

    with habbing.openHab(name="test", base="test", temp=True) as (hby, hab):
        cdb = basing.CueBaser(name="test_cb", temp=True)
        reger = viring.Reger(name="test", db=hby.db, temp=True)
        clock = [1000.0]
        client = make_client(metrics.Metrics(), hby, reger, cdb, ttl=30.0, clock=lambda: clock[0])

        client.simulate_get("/metrics")
        assert len(calls) == 1
        clock[0] += 10
        lines = client.simulate_get("/metrics").text.splitlines()
        assert len(calls) == 1  # within ttl, cached
        assert "sally_metrics_snapshot_age_seconds 10" in lines
        clock[0] += 25
        client.simulate_get("/metrics")
        assert len(calls) == 2  # ttl expired, refreshed


def test_metrics_endpoint_credentials(seeder, mockHelpingNowUTC, open_verification_context):
    """Verified LE/QVI credentials appear in the real endpoint's metrics snapshot."""
    with (open_verification_context(name="test", base="test", expiry=10_000_000) as context,
          dbing.openLMDB(cls=basing.CueBaser, name="test_cb", temp=True) as cdb):
        hby, reger = context.hby, context.reger
        seeder.load_schema(hby.db)

        issr = issuing.CredentialIssuer()
        issr.issue_legal_entity_vlei(seeder)
        load_credential(context, issuing.share_credential(issr.leeHab, issr.leeRgy, issr.lesaid))
        assert reger.saved.get(keys=(issr.lesaid,)) is not None

        client = make_client(metrics.Metrics(), hby, reger, cdb, ttl=0)
        lines = client.simulate_get("/metrics").text.splitlines()
        assert 'sally_credentials{status="issued",type="LE"} 1' in lines
        assert 'sally_credentials{status="issued",type="QVI"} 1' in lines
        assert 'sally_credentials{status="issued",type="unknown"} 0' in lines
        assert "sally_credentials_stored 2" in lines
        assert "sally_credentials_verified 2" in lines
        assert "sally_credentials_unverified 0" in lines
        assert "sally_credentials_missing_edges 0" in lines
        assert "sally_registries 2" in lines
