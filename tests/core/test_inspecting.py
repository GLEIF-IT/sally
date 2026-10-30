# -*- encoding: utf-8 -*-
"""
Tests for sally.core.inspecting
"""
import json

import pytest
from keri import kering
from keri.app import habbing
from keri.core import coring
from keri.db import dbing
from keri.vdr import eventing as veventing, viring

import issuing
from sally.core import basing, handling, inspecting


def load_credential(context, ims):
    """Feed one credential/TEL stream through the existing context and its escrow processors."""
    context.parser.parse(ims=ims)
    for _ in range(50):
        context.kvy.processEscrows()
        context.tvy.processEscrows()
        context.verifier.processEscrows()


def test_collect_and_export_round_trip(seeder, mockHelpingNowUTC, open_verification_context):
    """Export verified credentials and recover them in an independent destination context."""
    with (open_verification_context(name="test", base="test", expiry=10_000_000) as context,
          dbing.openLMDB(cls=basing.CueBaser, name="test_cb", temp=True) as cdb):
        hby, hab, reger = context.hby, context.hab, context.reger
        seeder.load_schema(hby.db)

        issr = issuing.CredentialIssuer()
        issr.issue_legal_entity_vlei(seeder)
        load_credential(context, issuing.share_credential(issr.leeHab, issr.leeRgy, issr.lesaid))
        assert reger.saved.get(keys=(issr.lesaid,)) is not None

        report = inspecting.collect(hby.db, reger, cdb)
        json.dumps(report)  # must be serializable

        assert [i["prefix"] for i in report["identifiers"]] == [hab.pre]
        assert len(report["registries"]) == 2  # QVI registry and the root registry that issued the QVI credential

        creds = {c["said"]: c for c in report["credentials"]}
        le = creds[issr.lesaid]
        qvisaid = le["edges"]["qvi"]
        assert set(creds) == {issr.lesaid, qvisaid}
        assert le["type"] == "LE"
        assert le["schema"] == handling.LE_SCHEMA
        assert le["status"] == inspecting.ISSUED
        assert le["verified"] is True
        assert le["telSn"] == 0
        assert le["missingEdges"] == []
        assert creds[qvisaid]["type"] == "QVI"
        assert creds[qvisaid]["status"] == inspecting.ISSUED

        assert report["escrows"]["telOutOfOrder"] == []
        assert report["pipeline"]["counts"]["iss"] == 0

        text = inspecting.formatReport(report)
        assert issr.lesaid in text and "LE issued" in text

        # --said filter
        only = inspecting.collect(hby.db, reger, cdb, saids=[qvisaid])
        assert [c["said"] for c in only["credentials"]] == [qvisaid]

        # Export from this instance and import into a fresh one: the migration path.
        stream = inspecting.exportCredentials(hby.db, reger)
        assert stream.count(issr.lesaid.encode()) > 0

        with open_verification_context(name="other", base="other", expiry=10_000_000) as destination:
            ohby, oreger = destination.hby, destination.reger
            seeder.load_schema(ohby.db)
            load_credential(destination, stream)

            assert oreger.saved.get(keys=(issr.lesaid,)) is not None
            assert oreger.saved.get(keys=(qvisaid,)) is not None
            other = inspecting.collect(ohby.db, oreger, cdb)
            migrated = {c["said"]: c for c in other["credentials"]}
            assert migrated[issr.lesaid]["status"] == inspecting.ISSUED
            assert migrated[issr.lesaid]["missingEdges"] == []


def test_collect_unknown_registry_and_out_of_order(seeder, mockHelpingNowUTC):
    with habbing.openHab(name="test", base="test", temp=True) as (hby, hab):
        cdb = basing.CueBaser(name="test_cb", temp=True)
        reger = viring.Reger(name="test", db=hby.db, temp=True)
        seeder.load_schema(hby.db)

        issr = issuing.CredentialIssuer()
        issr.issue_legal_entity_vlei(seeder)
        creder, *_ = issr.leeRgy.reger.cloneCred(said=issr.lesaid)

        # A revocation that arrives before anything else about the registry is escrowed out of order.
        rev = veventing.revoke(vcdig=creder.said, regk=creder.regi, dig=creder.said)
        tvy = veventing.Tevery(db=hby.db, reger=reger)
        with pytest.raises(kering.OutOfOrderError):
            tvy.processEvent(serder=rev, seqner=coring.Seqner(sn=1), saider=coring.Saider(qb64=creder.said))

        report = inspecting.collect(hby.db, reger, cdb)
        assert report["credentials"] == []
        ooo = report["escrows"]["telOutOfOrder"]
        assert len(ooo) == 1
        assert ooo[0]["prefix"] == creder.said
        assert ooo[0]["sn"] == 1
        assert ooo[0]["knownCredential"] is False

        # A credential whose registry this instance has never seen reports an unknown registry.
        reger.creds.pin(keys=(creder.said,), val=creder)
        rec = inspecting.credentialRecord(reger, creder)
        assert rec["status"] == inspecting.UNKNOWN_REGISTRY
        assert rec["verified"] is False


def test_collect_tel_only(seeder, mockHelpingNowUTC, open_verification_context):
    """TEL events (issuer KEL, registry, iss) that arrive without the ACDC show up as TEL only."""
    with (open_verification_context(name="test", base="test", expiry=10_000_000) as context,
          dbing.openLMDB(cls=basing.CueBaser, name="test_cb", temp=True) as cdb):
        hby, reger = context.hby, context.reger
        seeder.load_schema(hby.db)

        issr = issuing.CredentialIssuer()
        issr.issue_legal_entity_vlei(seeder)
        creder, *_ = issr.leeRgy.reger.cloneCred(said=issr.lesaid)

        ims = bytearray()
        for msg in issr.leeHab.db.clonePreIter(pre=creder.issuer):
            ims.extend(msg)
        for msg in issr.leeRgy.reger.clonePreIter(pre=creder.regi):
            ims.extend(msg)
        for msg in issr.leeRgy.reger.clonePreIter(pre=creder.said):
            ims.extend(msg)
        load_credential(context, bytes(ims))

        report = inspecting.collect(hby.db, reger, cdb)
        assert report["credentials"] == []
        assert len(report["registries"]) == 1
        assert report["telOnly"] == [dict(prefix=issr.lesaid, registry=creder.regi, status=inspecting.ISSUED,
                                          telSn=0, telTimestamp=report["telOnly"][0]["telTimestamp"])]
        assert "TEL only, no ACDC (1)" in inspecting.formatReport(report)

        # Once the ACDC itself arrives the credential moves out of TEL only.
        load_credential(context, issuing.share_credential(issr.leeHab, issr.leeRgy, issr.lesaid))
        report = inspecting.collect(hby.db, reger, cdb)
        assert report["telOnly"] == []
        assert issr.lesaid in {c["said"] for c in report["credentials"]}
