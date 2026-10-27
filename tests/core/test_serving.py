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
from sally.core import basing, handling, credentials

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
        assert creder.schema == handling.LE_SCHEMA
        assert prefixer.qb64 == qvi

        cues = decking.Deck()
        serder = veventing.revoke(vcdig=creder.said, regk=creder.regi, dig=creder.said)
        cues.append(dict(kin="revoked", serder=serder))
        tc = credentials.TeveryCuery(cdb=cdb, reger=reger, cues=cues)

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


def test_tevery_cuery_unknown_credential():
    """A revocation cue for a credential never presented to this instance is skipped, not fatal."""
    with habbing.openHab(name="test", base="test", temp=True) as (hby, hab):
        cdb = basing.CueBaser(name="test_cb", temp=True)
        reger = viring.Reger(temp=True)

        unknown = "EElymNmgs1u0mSaoCeOtSsNOROLuqOz103V3-4E-ClXH"
        regk = "EB-u4VAF7A7_GR8PXJoAVHv5X9vjtXew8Yo6Z3w9mQUQ"
        cues = decking.Deck()
        serder = veventing.revoke(vcdig=unknown, regk=regk, dig=unknown)
        cues.append(dict(kin="revoked", serder=serder))
        tc = credentials.TeveryCuery(cdb=cdb, reger=reger, cues=cues)

        doist = doing.Doist(limit=1.0, tock=0.25)
        doist.do(doers=[tc])  # raised AttributeError before the fix
        assert doist.tyme == 1.0

        assert len(cues) == 0
        assert cdb.snd.get(keys=(unknown,)) is None
        assert cdb.rev.get(keys=(unknown,)) is None
