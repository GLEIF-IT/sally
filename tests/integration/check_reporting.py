"""Exercise real Sally stores, scheduler and HTTP client against loopback sinks.

Run inside the test image with --network none. No witness, Harry, Sentry service,
production database, or host port is used. Test credentials supply valid CESR data.
"""
import argparse
import datetime
import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "tests/core")]

from hio.base import doing
from hio.help import decking
from keri.app import habbing
from keri.core import coring, serdering, parsing, eventing
from keri.help import helping
from keri.vdr import viring, verifying, eventing as veventing

from conftest import DbSeed
import issuing
from sally.app import reporting
from sally.core import basing, credentials, handling, serving


def load_credential(hby, reger, ims):
    kvy = eventing.Kevery(db=hby.db)
    tvy = veventing.Tevery(db=hby.db, reger=reger)
    vry = verifying.Verifier(hby=hby, reger=reger, expiry=10000000)
    parsing.Parser().parse(ims=ims, kvy=kvy, tvy=tvy, vry=vry)
    for _ in range(50):
        kvy.processEscrows()
        tvy.processEscrows()
        vry.processEscrows()
    return kvy, tvy, vry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sentry", action="store_true")
    parser.add_argument("--logs-level", choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"))
    args = parser.parse_args()
    if args.logs_level and not args.sentry:
        parser.error("--logs-level requires --sentry")
    args.output.mkdir(parents=True, exist_ok=True)
    events = []
    logs = []
    envelopes = []
    hooks = []
    hook_status = 200
    sink_status = 200
    rejected_envelopes = []
    release_silent = threading.Event()

    class Sink(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            if self.path.startswith("/api/1/envelope/"):
                if sink_status != 200:
                    rejected_envelopes.append(sink_status)
                    self.send_response(sink_status)
                    self.end_headers()
                    return
                if self.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                envelopes.append(raw.decode())
                lines = raw.splitlines()
                for index in range(1, len(lines), 2):
                    if json.loads(lines[index]).get("type") == "event":
                        events.append(json.loads(lines[index + 1]))
                    elif json.loads(lines[index]).get("type") == "log":
                        logs.extend(json.loads(lines[index + 1])["items"])
                self.send_response(200)
                self.end_headers()
            elif self.path == "/silent":
                release_silent.wait(20)
            else:
                hooks.append({"status": hook_status, "applied_downstream": False,
                              "body_sha256": hashlib.sha256(raw).hexdigest()})
                # HTTP receipt deliberately makes no claim about a downstream worker.
                self.send_response(hook_status)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

    sink = ThreadingHTTPServer(("127.0.0.1", 0), Sink)
    sink.daemon_threads = True
    thread = threading.Thread(target=sink.serve_forever, daemon=True)
    thread.start()
    port = sink.server_address[1]
    os.environ.pop("SENTRY_DSN", None)
    os.environ.pop("SALLY_SENTRY_LOG_LEVEL", None)
    if args.sentry:
        os.environ["SENTRY_DSN"] = f"http://public@127.0.0.1:{port}/1"
    if args.logs_level:
        os.environ["SALLY_SENTRY_LOG_LEVEL"] = args.logs_level
    os.environ["SENTRY_ENVIRONMENT"] = "test"
    os.environ["CLEAR_ESCROWS"] = "true"
    results = []

    with habbing.openHab(name="reporting-check", temp=True) as (hby, hab):
        cdb = basing.CueBaser(name="reporting-check", temp=True)
        reger = viring.Reger(name="reporting-check", db=hby.db, temp=True)
        paths = {"kel": hby.db.path, "pipeline": cdb.path, "credentials": reger.path}
        for store in (hby.db, cdb, reger):
            temp_root = Path(store.TempHeadDir).resolve()
            path = store.path
            if not store.temp: raise RuntimeError(f"Expected a temporary database, got persistent store {path}")
            if not Path(path).resolve().is_relative_to(temp_root): raise RuntimeError(f"Expected disposable store under {temp_root}, got {path}")
        (args.output / "database-identities.json").write_text(json.dumps(paths, indent=2) + "\n")

        original_now = helping.nowUTC
        helping.nowUTC = lambda: helping.fromIso8601("2021-01-01T00:00:00.000000+00:00")
        try:
            DbSeed.load_schema(hby.db)
            issuer = issuing.CredentialIssuer()
            issuer.issue_legal_entity_vlei(DbSeed)
            kvy, tvy, vry = load_credential(
                hby, reger, issuing.share_credential(issuer.qviHab, issuer.qviRgy, issuer.oorsaid))
        finally:
            helping.nowUTC = original_now
        creder = reger.creds.get(keys=(issuer.lesaid,))
        if creder is None: raise RuntimeError("Expected loaded LE test credential, got None")
        oor = reger.creds.get(keys=(issuer.oorsaid,))
        if oor is None: raise RuntimeError("Expected loaded OOR test credential, got None")
        auth_credential = next(c for _, c in issuer.leeRgy.reger.creds.getItemIter()
                               if c.schema == handling.OOR_AUTH_SCHEMA)

        def run(name, exercise):
            cdb.clearEscrows()
            comms = handling.Communicator(hby=hby, hab=hab, cdb=cdb, reger=reger,
                                          auth=issuer.extHab.pre, hook=f"http://127.0.0.1:{port}/hook",
                                          timeout=1, retry=0.1)
            start = len(events)
            start_hooks = len(hooks)
            outcome = {}
            with reporting.session():
                exercise(comms, outcome)
            captured = events[start:]
            (args.output / f"{name}.events.json").write_text(json.dumps(captured, indent=2) + "\n")
            result = dict(scenario=name, events=len(captured), pipeline=cdb.getCounts(),
                          webhook_receipts=hooks[start_hooks:], **outcome)
            results.append(result)
            return result

        def queue(comms, outcome, *, expired=False, credential=creder):
            date = helping.nowUTC() - datetime.timedelta(minutes=5 if expired else 0)
            cdb.recv.pin(keys=(credential.said, coring.Dater(dts=helping.toIso8601(date)).qb64), val=credential)

        def deliver(comms, outcome):
            queue(comms, outcome)
            serving.run_doers([comms], expire=1.8)

        success = run("http_200_without_downstream_proof", deliver)
        assert success["events"] == 0 and len(success["webhook_receipts"]) == 1 and success["pipeline"]["recv"] == 0

        def deliver_oor(comms, outcome):
            queue(comms, outcome, credential=oor)
            serving.run_doers([comms], expire=1.8)

        oor_success = run("oor_payload_delivery", deliver_oor)
        assert oor_success["events"] == 0 and oor_success["pipeline"]["recv"] == 0
        assert len(oor_success["webhook_receipts"]) == 1

        hook_status = 401
        failure = run("webhook_401", deliver)
        assert failure["pipeline"]["recv"] == 1
        assert len(failure["webhook_receipts"]) >= 1
        assert (failure["events"] >= 1) == args.sentry

        def drop(comms, outcome):
            queue(comms, outcome, expired=True)
            serving.run_doers([comms], expire=1.8)

        dropped = run("webhook_drop", drop)
        assert dropped["pipeline"]["recv"] == 0
        assert dropped["events"] == (1 if args.sentry else 0)
        if args.sentry:
            assert events[-1]["extra"]["dropped"] is True

        def silent(comms, outcome):
            comms.hook = f"http://127.0.0.1:{port}/silent"
            queue(comms, outcome, expired=True)
            serving.run_doers([comms], expire=1.8)

        stalled = run("silent_webhook_past_timeout", silent)
        assert stalled["events"] == 0 and stalled["pipeline"]["recv"] == 1

        def clear(comms, outcome):
            queue(comms, outcome)
            outcome["pending_before_clear"] = cdb.recv.cntAll()
            serving.clear_escrows(cdb)

        cleared = run("startup_clear", clear)
        assert cleared["events"] == 0 and cleared["pipeline"]["recv"] == 0

        def invalid_payload(comms, outcome):
            queue(comms, outcome, credential=auth_credential)
            loop = comms.escrowDo(tymth=lambda: 0.0)
            next(loop)
            next(loop)
            loop.close()

        swallowed = run("caught_escrow_exception", invalid_payload)
        assert swallowed["pipeline"]["recv"] == 1
        assert swallowed["events"] == (1 if args.sentry else 0)

        def revoked(comms, outcome):
            reg = issuer.qviRgy.regs[creder.regi]
            rev = reg.revoke(said=creder.said)
            seal = dict(i=creder.said, s=rev.snh, d=rev.said)
            anc = serdering.SerderKERI(raw=issuer.qviHab.interact(data=[seal]))
            kvy.processEvent(serder=anc, sigers=[issuer.qviHab.sign(ser=anc.raw, indexed=True)[0]])
            tvy.processEvent(serder=rev, seqner=coring.Seqner(sn=anc.sn), saider=coring.Saider(qb64=anc.said))
            cdb.snd.pin(keys=(creder.said,), val=coring.Prefixer(qb64=creder.issuer))
            cdb.iss.pin(keys=(creder.said,), val=coring.Dater())
            comms.processPresentations()

        rejected = run("already_revoked_presentation", revoked)
        assert rejected["pipeline"]["iss"] == 0 and rejected["pipeline"]["recv"] == 0
        assert rejected["events"] == (1 if args.sentry else 0)

        def unknown(comms, outcome):
            reger.creds.rem(keys=(creder.said,))
            rev = veventing.revoke(vcdig=creder.said, regk=creder.regi, dig=creder.said)
            tc = credentials.TeveryCuery(cdb=cdb, reger=reger,
                                        cues=decking.Deck([dict(kin="revoked", serder=rev)]))
            serving.run_doers([tc], expire=0.2)

        skipped = run("unknown_credential_revocation", unknown)
        assert skipped["pipeline"]["rev"] == 0
        assert skipped["events"] == (1 if args.sentry else 0)
        if args.sentry:
            assert "revocation received for unknown credential" in events[-1]["logentry"]["formatted"]

        sink_status = 503
        outage = run("sentry_unavailable", deliver)
        outage["rejected_envelopes"] = len(rejected_envelopes)
        assert outage["pipeline"]["recv"] == 1
        assert len(outage["webhook_receipts"]) >= 1
        assert outage["events"] == 0
        assert bool(rejected_envelopes) == args.sentry
        cdb.close(clear=True)
        reger.close(clear=True)

    release_silent.set()
    sink.shutdown()
    sink.server_close()
    if not args.logs_level:
        assert logs == []
    else:
        assert logs
    (args.output / "logs.json").write_text(json.dumps(logs, indent=2) + "\n")
    (args.output / "envelopes.json").write_text(json.dumps(envelopes, indent=2) + "\n")
    summary = dict(sentry=args.sentry, scenarios=results,
                   sdk_version=importlib.metadata.version("sentry-sdk") if args.sentry else None,
                   logs=len(logs), log_level=args.logs_level,
                   capture_policy="SDK event data and logging breadcrumbs retained; frame locals disabled.")
    log_text = json.dumps(logs)
    summary["data_exposure"] = {
        "credential_identifier_in_logs": creder.said in log_text,
        "fixture_person_name_in_logs": oor.attrib["personLegalName"] in log_text,
        "fixture_person_role_in_logs": oor.attrib["officialRole"] in log_text,
        "webhook_payload_in_logs": "Payload:" in log_text,
        "credential_identifier_in_events": creder.said in json.dumps(events),
        "fixture_person_name_in_events": oor.attrib["personLegalName"] in json.dumps(events),
        "webhook_payload_in_breadcrumbs": any(
            "Payload:" in crumb.get("message", "") for event in events
            for crumb in event.get("breadcrumbs", {}).get("values", [])),
    }
    if args.logs_level == "INFO":
        assert all(summary["data_exposure"].values())
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"sentry": args.sentry, "scenarios": len(results), "events": len(events),
                      "logs": len(logs), "assertions": "passed"}))


if __name__ == "__main__":
    main()
