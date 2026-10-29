# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.metrics module

In-process metrics registry and Prometheus text exposition formatter.

This module deliberately has no dependencies beyond the standard library so that it can be
imported from anywhere in the pipeline (handling, credentials) without creating import cycles.
The HTTP endpoint that serves the registry lives in sally.core.monitoring.
"""
import time

import sally

CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"

# Label values for sally_exceptions_total{kind=...}. One constant per site in the pipeline
# so that handling, credentials, and the tests all share a single spelling.
PRESENTATION_TIMEOUT = "presentation_timeout"
PRESENTATION_UNKNOWN_REGISTRY = "presentation_unknown_registry"
CREDENTIAL_REVOKED = "credential_revoked"
UNSUPPORTED_SCHEMA = "unsupported_schema"
QVI_UNKNOWN_ISSUER = "qvi_unknown_issuer"
SCHEMA_MISMATCH = "schema_mismatch"
MISSING_EDGE = "missing_edge"
CHAINED_CREDENTIAL_MISSING = "chained_credential_missing"
OOR_ATTRIBUTE_MISMATCH = "oor_attribute_mismatch"
REVOCATION_TIMEOUT = "revocation_timeout"
REVOCATION_UNKNOWN_REGISTRY = "revocation_unknown_registry"
REVOCATION_UNKNOWN_CREDENTIAL = "revocation_unknown_credential"
WEBHOOK_PAYLOAD_INVALID_SCHEMA = "webhook_payload_invalid_schema"
WEBHOOK_DROPPED = "webhook_dropped"
ESCROW_LOOP_ERROR = "escrow_loop_error"
NOTICE_IGNORED = "notice_ignored"

EXCEPTION_KINDS = (
    PRESENTATION_TIMEOUT,
    PRESENTATION_UNKNOWN_REGISTRY,
    CREDENTIAL_REVOKED,
    UNSUPPORTED_SCHEMA,
    QVI_UNKNOWN_ISSUER,
    SCHEMA_MISMATCH,
    MISSING_EDGE,
    CHAINED_CREDENTIAL_MISSING,
    OOR_ATTRIBUTE_MISMATCH,
    REVOCATION_TIMEOUT,
    REVOCATION_UNKNOWN_REGISTRY,
    REVOCATION_UNKNOWN_CREDENTIAL,
    WEBHOOK_PAYLOAD_INVALID_SCHEMA,
    WEBHOOK_DROPPED,
    ESCROW_LOOP_ERROR,
    NOTICE_IGNORED,
)

COUNTER = "counter"
GAUGE = "gauge"
UNLABELED_SERIES = ()

# Every metric family Sally exposes. Declaring them up front means a typo in an inc() or set()
# call raises KeyError instead of silently creating a new family, and fixes the output order.
CATALOGUE = (
    ("sally_info", GAUGE, "Sally build information. Always 1."),
    ("sally_process_start_time_seconds", GAUGE, "Unix time at which this Sally process started."),
    ("sally_pipeline_depth", GAUGE, "Entries in each stage of the webhook escrow pipeline."),
    ("sally_known_senders", GAUGE, "Distinct credentials for which a sender has been recorded."),
    ("sally_credentials_stored", GAUGE, "ACDCs held in the credential store."),
    ("sally_credentials_verified", GAUGE, "ACDCs that passed signature and chain verification."),
    ("sally_registries", GAUGE, "Credential registries (TELs) known to this instance."),
    ("sally_acdc_escrow", GAUGE, "ACDCs waiting in a keripy escrow, by reason."),
    ("sally_tel_escrow", GAUGE, "TEL events waiting in a keripy escrow, by reason."),
    ("sally_credentials", GAUGE, "Stored credentials by vLEI type and TEL status. "
                                "type=unknown means an unrecognised schema; status=unknown-registry or "
                                "no-tel-events means the issuance status cannot be determined."),
    ("sally_credentials_unverified", GAUGE, "Stored credentials that have not passed verification."),
    ("sally_credentials_missing_edges", GAUGE, "Stored credentials with at least one chained credential missing."),
    ("sally_tel_only_credentials", GAUGE, "Credentials with TEL events but no ACDC, "
                                         "typically revocations for credentials never presented here."),
    ("sally_tel_out_of_order_unknown", GAUGE, "Out-of-order TEL events for credentials not held by this instance."),
    ("sally_metrics_snapshot_duration_seconds", GAUGE, "Time taken by the last credential state walk."),
    ("sally_metrics_snapshot_age_seconds", GAUGE, "Age of the cached credential state snapshot at scrape time."),
    ("sally_exceptions_total", COUNTER, "Unknown or exceptional conditions hit by the pipeline, by kind."),
    ("sally_presentations_total", COUNTER, "Credential presentations that finished validation, by result."),
    ("sally_webhook_responses_total", COUNTER, "Responses received from the webhook, by action and outcome."),
    ("sally_revocations_total", COUNTER, "Revocation events queued for the webhook."),
)


def _escape(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _fmt(value):
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return repr(float(value))


class Family:
    """One metric family: a type, a help string, and its labelled series."""

    def __init__(self, name, kind, help):
        self.name = name
        self.kind = kind
        self.help = help
        self.series = {}  # tuple of (label, value) pairs, sorted by label -> number


class Metrics:
    """
    Minimal in-process metrics registry with Prometheus text exposition.

    hio runs everything on a single thread so no locking is needed.
    """

    def __init__(self):
        self.families = {name: Family(name, kind, help) for name, kind, help in CATALOGUE}
        self.started = time.time()
        self.set("sally_info", 1, version=sally.__version__)
        self.set("sally_process_start_time_seconds", self.started)
        # Pre-seed counters so that the first increment is visible to increase()/rate().
        for kind in EXCEPTION_KINDS:
            self.set("sally_exceptions_total", 0, kind=kind)
        for result in ("accepted", "rejected"):
            self.set("sally_presentations_total", 0, result=result)
        for action in ("iss", "rev"):
            for outcome in ("success", "failure"):
                self.set("sally_webhook_responses_total", 0, action=action, outcome=outcome)
        self.set("sally_revocations_total", 0)

    @staticmethod
    def _key(labels):
        if not labels:
            return UNLABELED_SERIES
        return tuple(sorted(labels.items()))

    def inc(self, name, amount=1, **labels):
        family = self.families[name]
        key = self._key(labels)
        family.series[key] = family.series.get(key, 0) + amount

    def set(self, name, value, **labels):
        self.families[name].series[self._key(labels)] = value

    def get(self, name, **labels):
        return self.families[name].series.get(self._key(labels))

    def clear(self, name):
        """Drop every series of a family, used before repopulating a gauge from a fresh snapshot."""
        self.families[name].series.clear()

    def render(self):
        """Render the registry in Prometheus text exposition format version 0.0.4."""
        lines = []
        for name, _, _ in CATALOGUE:
            family = self.families[name]
            if not family.series:
                continue
            lines.append(f"# HELP {name} {_escape(family.help)}")
            lines.append(f"# TYPE {name} {family.kind}")
            for key in sorted(family.series):
                value = family.series[key]
                if key:
                    labels = ",".join(f'{k}="{_escape(v)}"' for k, v in key)
                    lines.append(f"{name}{{{labels}}} {_fmt(value)}")
                else:
                    lines.append(f"{name} {_fmt(value)}")
        return "\n".join(lines) + "\n"
