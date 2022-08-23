# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.handling module

Handling support
"""
import os

import falcon
from hio.base import doing
from hio.core import http
from hio.help import decking
from keri.app import habbing
from keri.core import coring, parsing, eventing
from keri.help import helping
from keri.peer import exchanging
from keri.vdr import eventing as veventing, viring
from keri.vdr import verifying

from sally.core import handling, basing

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_presentation_handler():
    salt = coring.Salter(raw=b'abcdef0123456789').qb64
    with habbing.openHby(name="test", base="test", salt=salt) as hby:
        cdb = basing.CueBaser(name="test_cb")
        tvy = veventing.Tevery(db=hby.db)
        exc = exchanging.Exchanger(hby=hby, handlers=[])

        handling.loadHandlers(cdb=cdb, exc=exc, tvy=tvy)

        assert len(exc.routes) == 1
        assert exc.routes["/presentation"] is not None

        pre = "ECtWlHS2Wbx5M2Rg6nm69PCtzwb1veiRNvDpBGF9Z1Pc"
        said = "EJcjV4DalEqAtaOdlEcjNvo75HCs0lN5K3BbQwJ5kN6o"

        phan = exc.routes["/presentation"]
        phan.msgs.append(dict(payload=dict(i=pre,
                                           n=said)))
        limit = 1.0
        tock = 1.0
        doist = doing.Doist(limit=limit, tock=tock)
        doist.do(doers=[phan])
        assert doist.tyme == limit

        prefixer = cdb.snd.get(keys=(said,))
        assert prefixer is not None
        assert prefixer.qb64 == pre

        dater = cdb.iss.get(keys=(said,))
        assert dater is not None
        assert dater.datetime < helping.nowUTC()


def test_communicator(seeder):
    url = "http://localhost:5999/"
    salt = b'abcdef0123456789'
    root = "EWN6BzdXo6IByOsuh_fYanK300iEOrQKf6msmbIeC4Y0"
    qvi = "EY4ldIBDZP4Tpnm3RX320BO0yz8Uz2nUSN-C409GnCJM"
    leSchemaSaid = "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"
    oorSchemaSaid = "E2RzmSCFmG2a5U2OqZF-yUobeSYkW-a3FsN82eZXMxY0"
    lesaid = "E2FcBhZhvwXAO3-vUBKHHIwiZGeFENbyWRx0gZtBME9A"
    oorsaid = "EvydcrDPbJSmsHrIc50c-FW0v0VZQXwV6qA2MRDlvEp0"

    with habbing.openHab(name="test", base="test", salt=salt, temp=True) as (hby, hab):
        cdb = basing.CueBaser(name="test_cb", temp=True)
        reger = viring.Reger(temp=True)
        kvy = eventing.Kevery(db=hby.db)
        tvy = veventing.Tevery(db=hby.db, reger=reger)
        vry = verifying.Verifier(hby=hby, reger=tvy.reger, expiry=10000000)
        msgs = decking.Deck()
        httpDoer = launch_mock_server(msgs=msgs)
        comms = handling.Communicator(hby=hby, hab=hab, cdb=cdb, reger=tvy.reger, hook=url, auth=root)

        seeder.load_schema(hby.db)

        # Load file containing entire chain for issued and valid Legal Entity credential
        f = open(os.path.join(TEST_DIR, "legal-entity-vlei.cesr"))
        le = f.read()
        assert len(le) == 8020

        # Parse all LE artifacts
        parsing.Parser().parse(ims=bytearray(le.encode("utf-8")), kvy=kvy, tvy=tvy, vry=vry)

        saider = tvy.reger.saved.get(keys=(lesaid,))
        assert saider is not None
        creder = tvy.reger.creds.get(keys=(lesaid,))
        assert creder is not None

        prefixer = coring.Prefixer(qb64=creder.issuer)
        assert creder.said == lesaid
        assert creder.schema == leSchemaSaid
        assert prefixer.qb64 == qvi

        # Replicate a presentation of the LE credential
        now = coring.Dater()
        cdb.snd.pin(keys=(creder.said,), val=prefixer)
        cdb.iss.pin(keys=(creder.said,), val=now)

        doers = [httpDoer, comms]

        limit = 2.0
        tock = 0.25
        doist = doing.Doist(limit=limit, tock=tock)
        doist.do(doers=doers)
        assert doist.tyme == limit

        assert len(msgs) == 1
        req = msgs.popleft()
        assert req.headers["SALLY-RESOURCE"] == creder.schema
        assert "SIGNATURE" in req.headers
        assert "SALLY-TIMESTAMP" in req.headers
        data = req.get_media()
        assert data == {'action': 'iss',
                        'actor': 'EY4ldIBDZP4Tpnm3RX320BO0yz8Uz2nUSN-C409GnCJM',
                        'data': {'LEI': '5493001KJTIIGC8Y1R17',
                                 'credential': 'E2FcBhZhvwXAO3-vUBKHHIwiZGeFENbyWRx0gZtBME9A',
                                 'issueTimestamp': '2022-08-22T21:02:31.049303+00:00',
                                 'issuer': 'EY4ldIBDZP4Tpnm3RX320BO0yz8Uz2nUSN-C409GnCJM',
                                 'qviCredential': 'EQmMF4GCwO0JK6aXSj8ZXGq5qCQMmdKOD2jsvYDWADMQ',
                                 'recipient': 'EKXPX7hWw8KK5Y_Mxs2TOuCrGdN45vPIZ78NofRlVBws',
                                 'schema': 'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs'}}

        # Load file containing entire chain for issued and valid OOR credential
        f = open(os.path.join(TEST_DIR, "oor-vlei.cesr"))
        oor = f.read()
        assert len(oor) == 17736

        # Parse all OOR artifacts
        parsing.Parser().parse(ims=bytearray(oor.encode("utf-8")), kvy=kvy, tvy=tvy, vry=vry)

        saider = tvy.reger.saved.get(keys=(oorsaid,))
        assert saider is not None
        creder = tvy.reger.creds.get(keys=(oorsaid,))
        assert creder is not None

        prefixer = coring.Prefixer(qb64=creder.issuer)
        assert creder.said == oorsaid
        assert creder.schema == oorSchemaSaid
        assert prefixer.qb64 == qvi

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
        assert "SIGNATURE" in req.headers
        assert "SALLY-TIMESTAMP" in req.headers
        data = req.get_media()
        assert data == {'action': 'iss',
                        'actor': 'EY4ldIBDZP4Tpnm3RX320BO0yz8Uz2nUSN-C409GnCJM',
                        'data': {'LEI': '6383001AJTYIGC8Y1X37',
                                 'credential': 'EvydcrDPbJSmsHrIc50c-FW0v0VZQXwV6qA2MRDlvEp0',
                                 'issueTimestamp': '2022-08-22T21:02:42.203424+00:00',
                                 'issuer': 'EY4ldIBDZP4Tpnm3RX320BO0yz8Uz2nUSN-C409GnCJM',
                                 'legalEntityCredential': 'E2FcBhZhvwXAO3-vUBKHHIwiZGeFENbyWRx0gZtBME9A',
                                 'officialRole': 'Chief Executive Officer',
                                 'personLegalName': 'John Smith',
                                 'qviCredential': 'EQmMF4GCwO0JK6aXSj8ZXGq5qCQMmdKOD2jsvYDWADMQ',
                                 'recipient': 'Esf8b_AngI1d0KbOFjPGIfpVani0HTagWeaYTLs14PlE',
                                 'schema': 'E2RzmSCFmG2a5U2OqZF-yUobeSYkW-a3FsN82eZXMxY0'}}


def launch_mock_server(port=5999, msgs=None):
    app = falcon.App(
        middleware=falcon.CORSMiddleware(
            allow_origins='*',
            allow_credentials='*',
            expose_headers=['cesr-attachment', 'cesr-date', 'content-type']))
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
