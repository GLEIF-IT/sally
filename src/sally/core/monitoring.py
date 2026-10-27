import time

import falcon
import sally
from keri.help import nowIso8601

from sally import ogler, log_name
from sally.core import handling, inspecting, metrics as metricsmod

logger = ogler.getLogger(log_name)

CREDENTIAL_TYPES = tuple(sorted(set(handling.type_to_name.values()))) + ("unknown",)
CREDENTIAL_STATUSES = (inspecting.ISSUED, inspecting.REVOKED, inspecting.NO_TEL, inspecting.UNKNOWN_REGISTRY)


class HealthEnd:
    """
    Basic health check endpoint including a health message, Sally version, and operational metrics
    """

    def __init__(self, cdb = None):
        """
        Adds the CueBaser to allow getting metric counts.
        Defaults to none in case used via demo webhook
        """
        self.cdb = cdb


    def on_get(self, req, resp):
        counts = self.cdb.getCounts() if self.cdb else {}
        resp.status = falcon.HTTP_OK
        resp.media = {
            "message": f"Health is okay. Time is {nowIso8601()}",
            "version": f"{sally.__version__}",
            "counts": counts
        }


class MetricsEnd:
    """
    Prometheus text exposition endpoint.

    Cheap gauges (pipeline depths, escrow sizes) are counted with LMDB cursors on every scrape.
    The credential walk that classifies every ACDC by type and status is more expensive, so its
    result is cached for `ttl` seconds. In-process counters live in the shared Metrics registry.
    """

    def __init__(self, metrics, db, reger, cdb, ttl=30.0, clock=time.monotonic):
        """
        Parameters:
            metrics (Metrics): shared registry also incremented by the pipeline doers
            db (Baser): KEL store
            reger (Reger): credential and TEL store
            cdb (CueBaser): webhook escrow pipeline store
            ttl (float): seconds to cache the credential state snapshot
            clock (callable): monotonic clock, injectable for tests
        """
        self.metrics = metrics
        self.db = db
        self.reger = reger
        self.cdb = cdb
        self.ttl = ttl
        self.clock = clock
        self.snapshotAt = None

    def on_get(self, req, resp):
        self.collectCheap()
        now = self.clock()
        if self.snapshotAt is None or now - self.snapshotAt > self.ttl:
            self.refreshSnapshot()
            now = self.clock()
        self.metrics.set("sally_metrics_snapshot_age_seconds", now - self.snapshotAt)

        resp.status = falcon.HTTP_OK
        resp.content_type = metricsmod.CONTENT_TYPE
        resp.text = self.metrics.render()

    def collectCheap(self):
        """Gauges that only need an LMDB cursor count, no deserialization."""
        m = self.metrics
        cdb = self.cdb
        reger = self.reger

        for stage in ("iss", "rev", "recv", "revk", "ack"):
            m.set("sally_pipeline_depth", getattr(cdb, stage).cntAll(), stage=stage)
        m.set("sally_known_senders", cdb.snd.cntAll())

        m.set("sally_credentials_stored", reger.creds.cntAll())
        m.set("sally_credentials_verified", reger.saved.cntAll())
        m.set("sally_registries", reger.states.cntAll())

        m.set("sally_acdc_escrow", reger.mre.cntAll(), reason="missing_registry")
        m.set("sally_acdc_escrow", reger.mce.cntAll(), reason="missing_chain")
        m.set("sally_acdc_escrow", reger.mse.cntAll(), reason="missing_schema")
        m.set("sally_acdc_escrow", reger.cmse.cntAll(), reason="missing_signature")

        m.set("sally_tel_escrow", reger.cnt(db=reger.oots), reason="out_of_order")
        m.set("sally_tel_escrow", reger.cnt(db=reger.twes), reason="partial_witness")
        m.set("sally_tel_escrow", reger.cnt(db=reger.taes), reason="anchorless")

    def refreshSnapshot(self):
        """Walk every stored credential and classify it; cached for ttl seconds."""
        m = self.metrics
        start = self.clock()
        summary = inspecting.summarize(inspecting.collect(self.db, self.reger, self.cdb))

        m.clear("sally_credentials")
        for ctype in CREDENTIAL_TYPES:
            for status in CREDENTIAL_STATUSES:
                m.set("sally_credentials", 0, type=ctype, status=status)
        for (ctype, status), count in summary["credentials"].items():
            m.set("sally_credentials", count, type=ctype, status=status)

        m.set("sally_credentials_unverified", summary["unverified"])
        m.set("sally_credentials_missing_edges", summary["missingEdges"])
        m.set("sally_tel_only_credentials", summary["telOnly"])
        m.set("sally_tel_out_of_order_unknown", summary["telOutOfOrderUnknown"])

        self.snapshotAt = self.clock()
        m.set("sally_metrics_snapshot_duration_seconds", self.snapshotAt - start)
