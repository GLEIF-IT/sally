

# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.serving module

Handling support
"""
import os

import falcon
from hio.base import doing
from hio.core import http
from hio.help import decking
from keri.app import habbing
from keri.core import coring, parsing, eventing, scheming
from keri.help import helping
from keri.peer import exchanging
from keri.vdr import eventing as veventing, viring
from keri.vdr import verifying

from core.test_handling import load_schema
from sally.core import handling, basing, serving

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_tevery_cuery():
    qvi = "EY4ldIBDZP4Tpnm3RX320BO0yz8Uz2nUSN-C409GnCJM"
    schemaSaid = "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"
    said = "E2FcBhZhvwXAO3-vUBKHHIwiZGeFENbyWRx0gZtBME9A"

    with habbing.openHab(name="test", base="test", temp=True) as (hby, hab):
        cdb = basing.CueBaser(name="test_cb", temp=True)
        reger = viring.Reger(temp=True)
        kvy = eventing.Kevery(db=hby.db)
        tvy = veventing.Tevery(db=hby.db, reger=reger)
        vry = verifying.Verifier(hby=hby, reger=tvy.reger, expiry=10000000)

        load_schema(hby.db)

        # Load file containing entire chain for issued and valid Legal Entity credential
        f = open(os.path.join(TEST_DIR, "legal-entity-vlei.cesr"))
        le = f.read()
        assert len(le) == 8020

        # Parse all LE artifacts
        parsing.Parser().parse(ims=bytearray(le.encode("utf-8")), kvy=kvy, tvy=tvy, vry=vry)

        saider = tvy.reger.saved.get(keys=(said,))
        assert saider is not None
        creder = tvy.reger.creds.get(keys=(said,))
        assert creder is not None

        prefixer = coring.Prefixer(qb64=creder.issuer)
        assert creder.said == said
        assert creder.schema == schemaSaid
        assert prefixer.qb64 == qvi

        cues = decking.Deck()
        serder = veventing.revoke(vcdig=creder.said, regk=creder.status, dig=creder.said)
        cues.append(dict(kin="revoked", serder=serder))
        tc = serving.TeveryCuery(cdb=cdb, reger=reger, cues=cues)

        limit = 1.0
        tock = 0.25
        doist = doing.Doist(limit=limit, tock=tock)
        doist.do(doers=[tc])
        assert doist.tyme == limit

        prefixer = cdb.snd.get(keys=(creder.said,))
        assert prefixer is not None
        assert prefixer.qb64 == qvi
        dater = cdb.rev.get(keys=(creder.said,))
        assert dater is not None
        assert dater.datetime < helping.nowUTC()

