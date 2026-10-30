# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.handling module

Handling support
"""
import falcon
from hio.base import doing
from hio.core import http
from hio.help import decking
from keri.app import notifying
from keri.core import coring
from keri.help import helping
from keri.db import dbing
from keri.vc import protocoling
from sally.core import handling, basing, httping, metrics

import issuing


def test_presentation_handler(seeder, mockHelpingNowUTC, open_verification_context):
    """An IPEX grant reaches the presentation escrow through the real parser and handlers."""
    with (open_verification_context(
            name="test", base="test", salt=b'abcdef0123456789', expiry=10_000_000,
          ) as context,
          dbing.openLMDB(cls=basing.CueBaser, name="test_cb", temp=True) as cdb,
          dbing.openLMDB(cls=notifying.Noter, name="test", temp=True) as noter):
        hby, parser = context.hby, context.parser
        # This test owns the IPEX notification and presentation handlers.
        notifier = notifying.Notifier(hby=hby, noter=noter)
        protocoling.loadHandlers(hby=hby, exc=context.exc, notifier=notifier)

        seeder.load_schema(hby.db)
        # Load file containing entire chain for issued and valid Legal Entity credential
        issr = issuing.CredentialIssuer()
        issr.issue_legal_entity_vlei(seeder)

        grant, atc = issr.grant_legal_entity_vlei()
        print(grant.pretty())

        doers = handling.loadHandlers(
            cdb=cdb,
            hby=hby,
            notifier=notifier,
            parser=parser,
        )

        msgs = bytearray()
        for msg in issr.qviHab.db.clonePreIter(pre=issr.qviHab.pre):
            msgs.extend(msg)

        parser.parse(ims=bytes(msgs))

        ims = grant.raw + atc
        parser.parse(ims=ims)

        limit = 1.0
        tock = 1.0
        doist = doing.Doist(limit=limit, tock=tock, doers=doers)

        doist.enter()

        doist.recur()

        doist.exit()

        prefixer = cdb.snd.get(keys=(issr.lesaid,))
        assert prefixer is not None
        assert prefixer.qb64 == issr.qviHab.pre

        dater = cdb.iss.get(keys=(issr.lesaid,))
        assert dater is not None
        assert dater.datetime == helping.fromIso8601("2021-01-01T00:00:00.000000+00:00")


def test_communicator(seeder, mockHelpingNowUTC, open_verification_context):
    """Verified LE/OOR presentations produce signed webhooks with their expected payloads."""
    url = "http://localhost:5999/"
    salt = b'abcdef0123456789'
    root = "EID5n0m83IVIra_VZhSpov4RG7D9gxBnZeNPTlJK40TM"

    with (open_verification_context(name="test", base="test", salt=salt, expiry=10_000_000) as context,
          dbing.openLMDB(cls=basing.CueBaser, name="test_cb", temp=True) as cdb):
        hby, hab = context.hby, context.hab
        kvy, tvy, vry = context.kvy, context.tvy, context.verifier
        msgs = decking.Deck()
        httpDoer = launch_mock_server(msgs=msgs)
        m = metrics.Metrics()
        comms = handling.Communicator(hby=hby, hab=hab, cdb=cdb, reger=tvy.reger, hook=url, auth=root, retry=0.25,
                                      metrics=m)

        seeder.load_schema(hby.db)

        # Issue up to legal entity credential
        issr = issuing.CredentialIssuer()
        issr.issue_legal_entity_vlei(seeder)

        ims = issuing.share_credential(issr.leeHab, issr.leeRgy, issr.lesaid)
        context.parser.parse(ims=ims)

        while not tvy.reger.saved.get(keys=(issr.lesaid,)):
            kvy.processEscrows()
            tvy.processEscrows()
            vry.processEscrows()

        saider = tvy.reger.saved.get(keys=(issr.lesaid,))
        assert saider is not None
        creder = tvy.reger.creds.get(keys=(issr.lesaid,))
        assert creder is not None

        prefixer = coring.Prefixer(qb64=creder.issuer)
        assert creder.said == issr.lesaid
        assert creder.schema == handling.LE_SCHEMA
        assert prefixer.qb64 == issr.qviHab.pre

        # Replicate a presentation of the LE credential
        now = coring.Dater()
        cdb.snd.pin(keys=(creder.said,), val=prefixer)
        cdb.iss.pin(keys=(creder.said,), val=now)

        doers = [httpDoer, comms]

        limit = 5.0
        tock = 0.25
        doist = doing.Doist(limit=limit, tock=tock)
        doist.do(doers=doers)
        assert doist.tyme == limit

        assert len(msgs) == 1
        assert m.get("sally_presentations_total", result="accepted") == 1
        assert m.get("sally_presentations_total", result="rejected") == 0
        assert m.get("sally_webhook_responses_total", action="iss", outcome="success") == 1
        req = msgs.popleft()
        assert req.headers["SALLY-RESOURCE"] == creder.schema
        assert req.headers["SIGNATURE-INPUT"] == ('sig0=("sally-resource" "@method" "@path" '
                                                  '"sally-timestamp");created=1609459200;keyid="ILWsN7_dmckaGB4kS-S50PB'
                                                  'nUi1KzvFq5Tkg1DoIa6s=";alg="ed25519"')
        assert "SIGNATURE" in req.headers
        assert "SALLY-TIMESTAMP" in req.headers
        data = req.get_media()
        assert data == {'action': 'iss',
                        'actor': 'EOwXzTKWgsmCDVJwMS4VUJWX-m-oKx9d8VDyaRNY6mMZ',
                        'data': {'LEI': '5493001KJTIIGC8Y1R17',
                                 'credential': 'EL5nGzlXb8DEjFh4pOZMd7F10NYfX7inyci3iw9juY6_',
                                 'issueTimestamp': '2021-01-01T00:00:00.000000+00:00',
                                 'issuer': 'EOwXzTKWgsmCDVJwMS4VUJWX-m-oKx9d8VDyaRNY6mMZ',
                                 'qviCredential': 'EIbjVgfyrIj_jVjpgZXu2D-FFwWIc-pCFWnNd3F_vrD2',
                                 'recipient': 'EI0QTANut9IcXuPDbr7la4JJrjhMZ-EEk5q7Ahds8qBa',
                                 'schema': 'ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY',
                                 'type': 'LE'}}

        ims = issuing.share_credential(issr.qviHab, issr.qviRgy, issr.oorsaid)
        context.parser.parse(ims=ims)

        while not tvy.reger.saved.get(keys=(issr.oorsaid,)):
            kvy.processEscrows()
            tvy.processEscrows()
            vry.processEscrows()

        creder = tvy.reger.creds.get(keys=(issr.oorsaid,))
        assert creder is not None

        prefixer = coring.Prefixer(qb64=creder.issuer)
        assert creder.said == issr.oorsaid
        assert creder.schema == handling.OOR_SCHEMA
        assert prefixer.qb64 == issr.qviHab.pre

        # Replicate a presentation of the OOR credential
        now = coring.Dater()
        cdb.snd.pin(keys=(creder.said,), val=prefixer)
        cdb.iss.pin(keys=(creder.said,), val=now)

        doers = [httpDoer, comms]

        limit = 3.0
        tock = 0.25
        doist = doing.Doist(limit=limit, tock=tock)
        doist.do(doers=doers)
        assert doist.tyme == limit

        assert len(msgs) == 1
        req = msgs.popleft()
        assert req.headers["SALLY-RESOURCE"] == creder.schema
        assert req.headers["SIGNATURE-INPUT"] == ('sig0=("sally-resource" "@method" "@path" '
                                                  '"sally-timestamp");created=1609459200;keyid="ILWsN7_dmckaGB4kS-S50PB'
                                                  'nUi1KzvFq5Tkg1DoIa6s=";alg="ed25519"')
        assert "SIGNATURE" in req.headers
        assert "SALLY-TIMESTAMP" in req.headers

        data = req.get_media()
        assert data == {'action': 'iss',
                        'actor': 'EOwXzTKWgsmCDVJwMS4VUJWX-m-oKx9d8VDyaRNY6mMZ',
                        'data': {'LEI': '5493001KJTIIGC8Y1R17',
                                 'authCredential': 'EM4Q5HNAiVZGqzPL1BJVGF0GCIUYng07kFIz49dC7n2c',
                                 'credential': 'EHZ05NsGCdWNujHTK3FqyuPmR8qz04Q3xg3Hnz1hkPmm',
                                 'issueTimestamp': '2021-01-01T00:00:00.000000+00:00',
                                 'issuer': 'EOwXzTKWgsmCDVJwMS4VUJWX-m-oKx9d8VDyaRNY6mMZ',
                                 'legalEntityCredential': 'EL5nGzlXb8DEjFh4pOZMd7F10NYfX7inyci3iw9juY6_',
                                 'officialRole': 'Baba Yaga',
                                 'personLegalName': 'John Wick',
                                 'qviCredential': 'EIbjVgfyrIj_jVjpgZXu2D-FFwWIc-pCFWnNd3F_vrD2',
                                 'recipient': 'EIf2fK7M9Mfd-Twv2Ig3n8PpGM_p976mciznHoknVPLs',
                                 'schema': 'EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy',
                                 'type': 'OOR'}}


def launch_mock_server(port=5999, msgs=None):
    app = falcon.App(
        middleware=falcon.CORSMiddleware(
            allow_origins='*',
            allow_credentials='*',
            expose_headers=httping.cesr_headers()))
    app.add_route("/", MockListener(msgs=msgs))

    server = http.Server(port=port, app=app)
    httpServerDoer = http.ServerDoer(server=server)

    return httpServerDoer


class MockListener:
    """
    Endpoint for web hook calls that prints events to stdout
    """

    def __init__(self, msgs=None):
        self.msgs = msgs if msgs is not None else decking.Deck()

    def on_post(self, req, rep):
        self.msgs.append(req)
        rep.status = falcon.HTTP_200
