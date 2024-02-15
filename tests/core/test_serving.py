

# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.serving module

Handling support
"""
import os

from hio.base import doing
from hio.help import decking
from keri.app import habbing
from keri.core import coring, parsing, eventing
from keri.help import helping
from keri.vdr import eventing as veventing, viring
from keri.vdr import verifying

import issuing
from sally.core import basing, serving, handling

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_tevery_cuery(seeder, mockHelpingNowUTC):
    qvi = "EOwXzTKWgsmCDVJwMS4VUJWX-m-oKx9d8VDyaRNY6mMZ"

    with habbing.openHab(name="test", base="test", temp=True) as (hby, hab):
        cdb = basing.CueBaser(name="test_cb", temp=True)
        reger = viring.Reger(temp=True)
        kvy = eventing.Kevery(db=hby.db)
        tvy = veventing.Tevery(db=hby.db, reger=reger)
        vry = verifying.Verifier(hby=hby, reger=tvy.reger, expiry=10000000)

        seeder.load_schema(hby.db)

        # Load file containing entire chain for issued and valid Legal Entity credential
        issr = issuing.CredentialIssuer()
        issr.issue_legal_entity_vlei(seeder)

        ims = issuing.share_credential(issr.leeHab, issr.leeRgy, issr.lesaid)
        parsing.Parser().parse(ims=ims, kvy=kvy, tvy=tvy, vry=vry)

        while not tvy.reger.saved.get(keys=(issr.lesaid,)):
            kvy.processEscrows()
            tvy.processEscrows()
            vry.processEscrows()

        creder = tvy.reger.creds.get(keys=(issr.lesaid,))
        assert creder is not None

        prefixer = coring.Prefixer(qb64=creder.issuer)
        assert creder.said == issr.lesaid
        assert creder.schema == handling.LE_SCHEMA[0]
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
        assert dater.datetime == helping.nowUTC()  # mocked to return the same date

