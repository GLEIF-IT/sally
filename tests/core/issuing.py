# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.handling module

Handling support
"""

import json
import os

from keri.app import habbing, signing
from keri.core import coring, parsing, eventing, serdering
from keri.core.eventing import SealEvent
from keri.vdr import credentialing
from keri.vdr import verifying
from keri.vc import protocoling
from keri.help import helping

from sally.core import handling

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class CredentialIssuer:
    extsalt = b'0ACDEyMzQ1Njc4OWxtbm9GhI'
    qvisalt = b'0ACDEyMzQ1Njc4OWxtbm9aBc'
    leesalt = b'0ACDEyMzQ1Njc4OWxtbm9AbC'
    persalt = b'0ACDEyMzQ1Njc4OWxtbm9dEf'
    extnonce = "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s"
    qvinonce = "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2t"
    leenonce = "AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2u"

    def __init__(self):
        self.lesaid = ""
        self.oorsaid = ""
        self.extHby, self.extHab = openHab(name="ext", temp=True, salt=self.extsalt)
        self.qviHby, self.qviHab = openHab(name="qvi", temp=True, salt=self.qvisalt)
        self.leeHby, self.leeHab = openHab(name="lee", temp=True, salt=self.leesalt)
        self.perHby, self.perHab = openHab(name="per", temp=True, salt=self.persalt)
        self.extRgy = credentialing.Regery(hby=self.extHby, name=self.extHab.name, temp=True)
        self.qviRgy = credentialing.Regery(hby=self.qviHby, name=self.qviHab.name, temp=True)
        self.leeRgy = credentialing.Regery(hby=self.leeHby, name=self.leeHab.name, temp=True)

        assert self.extHab.pre == "EID5n0m83IVIra_VZhSpov4RG7D9gxBnZeNPTlJK40TM"
        assert self.qviHab.pre == "EOwXzTKWgsmCDVJwMS4VUJWX-m-oKx9d8VDyaRNY6mMZ"
        assert self.leeHab.pre == "EI0QTANut9IcXuPDbr7la4JJrjhMZ-EEk5q7Ahds8qBa"
        assert self.perHab.pre == "EIf2fK7M9Mfd-Twv2Ig3n8PpGM_p976mciznHoknVPLs"

    def grant_legal_entity_vlei(self):
        creder, prefixer, seqner, saider = self.qviRgy.reger.cloneCred(said=self.lesaid)
        acdc = signing.serialize(creder, prefixer, seqner, saider)
        iss = self.qviRgy.reger.cloneTvtAt(creder.said)

        iserder = serdering.SerderKERI(raw=bytes(iss))  # coring.Serder(raw=bytes(iss))
        seqner = coring.Seqner(sn=iserder.sn)

        serder = self.qviHby.db.findAnchoringSealEvent(creder.sad['i'],
                                                    seal=dict(i=iserder.pre, s=seqner.snh, d=iserder.said))
        anc = self.qviHby.db.cloneEvtMsg(pre=serder.pre, fn=0, dig=serder.said)

        grant, atc = protocoling.ipexGrantExn(hab=self.qviHab, recp=self.leeHab.pre, message="a string", acdc=acdc,
                                            iss=iss, anc=anc,dt=helping.nowIso8601())
        return grant, atc

    def issue_legal_entity_vlei(self, seeder):
        extKvy = eventing.Kevery(db=self.extHab.db)
        qviKvy = eventing.Kevery(db=self.qviHab.db)
        leeKvy = eventing.Kevery(db=self.leeHab.db)
        perKvy = eventing.Kevery(db=self.perHab.db)

        seeder.load_schema(self.extHby.db)
        seeder.load_schema(self.qviHby.db)
        seeder.load_schema(self.leeHby.db)
        seeder.load_schema(self.perHby.db)

        habs = [self.extHab, self.qviHab, self.leeHab, self.perHab]
        kvys = [extKvy, qviKvy, leeKvy, perKvy]

        # Introduce everyone
        for hab in habs:
            icp = hab.makeOwnEvent(sn=0)
            for kvy in kvys:
                if kvy.db.path == hab.db.path:
                    continue
                parsing.Parser().parse(ims=bytearray(icp), kvy=kvy)

                # Verifying everyone knows about each other
                assert hab.pre in kvy.db.kevers

        extVer = verifying.Verifier(hby=self.extHby, reger=self.extRgy.reger)
        qviVer = verifying.Verifier(hby=self.qviHby, reger=self.qviRgy.reger)
        leeVer = verifying.Verifier(hby=self.leeHby, reger=self.leeRgy.reger)

        extRegy, extRar = create_registry(self.extHby, self.extHab, self.extRgy, self.extnonce)
        assert extRegy.regk == "EOKOThFjIuJI7DJfkXbtwX1RvR3SpsW6NGcSfLRvCvcb"
        qviRegy, qviRar = create_registry(self.qviHby, self.qviHab, self.qviRgy, self.qvinonce)
        assert qviRegy.regk == "EJMOkHVq8AwHmtHV9FJ7FgN3EMKswFChk5bHvS4rUZbb"
        leeRegy, leeRar = create_registry(self.leeHby, self.leeHab, self.leeRgy, self.leenonce)
        assert leeRegy.regk == "ENOrkGZwBUI0_659sDjAW14nAg2Hoqf7qk_TNTIFb-7n"

        # Issue QVI credential from EXT to QVI
        extCred = credentialing.Credentialer(hby=self.extHby, rgy=self.extRgy, registrar=extRar, verifier=extVer)
        creder = extCred.create(regname=self.extRgy.name,
                                recp=self.qviHab.pre,
                                schema=handling.QVI_SCHEMA,
                                source=None,
                                rules=None,
                                data=dict(LEI="6383001AJTYIGC8Y1X37"),
                                private=False)
        iserder = extRegy.issue(said=creder.said)
        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])
        rseal = eventing.SealEvent(vcid, rseq.snh, iserder.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        anc = self.extHab.interact(data=[rseal])
        aserder = serdering.SerderKERI(raw=anc)

        extCred.issue(creder=creder, serder=iserder)
        extRar.issue(creder=creder, iserder=iserder, anc=aserder)

        while not self.extRgy.reger.saved.get(creder.said):
            self.extRgy.processEscrows()
            extRar.processEscrows()
            extVer.processEscrows()
            extCred.processEscrows()

        assert creder.said == "EIbjVgfyrIj_jVjpgZXu2D-FFwWIc-pCFWnNd3F_vrD2"

        # Parse the credential and all its crypto goodness
        parsing.Parser().parse(ims=share_credential(self.extHab, self.extRgy, creder.said),
                               kvy=qviKvy, tvy=qviVer.tvy, vry=qviVer)

        while not self.qviRgy.reger.saved.get(creder.said):
            qviKvy.processEscrows()
            self.qviRgy.processEscrows()
            qviRar.processEscrows()
            qviVer.processEscrows()

        issd = self.qviRgy.reger.saved.get(creder.said)
        assert issd.qb64 == creder.said

        # Issue Legal Entity Credential from QVI to LE
        # Create edges pointing back to QVI credential
        edges = dict(d="", qvi=dict(n=creder.said, s=handling.QVI_SCHEMA))
        _, edges = coring.Saider.saidify(sad=edges, label=coring.Saids.d)

        # Load rules section
        f = open(os.path.join(TEST_DIR, "rules.json"))
        r = f.read()
        assert len(r) == 932
        rules = json.loads(r)

        qviCred = credentialing.Credentialer(hby=self.qviHby, rgy=self.qviRgy, registrar=qviRar, verifier=qviVer)
        creder = qviCred.create(regname=self.qviRgy.name,
                                recp=self.leeHab.pre,
                                schema=handling.LE_SCHEMA,
                                source=edges,
                                rules=rules,
                                data=dict(LEI="5493001KJTIIGC8Y1R17"),
                                private=False)
        iserder = qviRegy.issue(said=creder.said)
        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])
        rseal = eventing.SealEvent(vcid, rseq.snh, iserder.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        anc = self.qviHab.interact(data=[rseal])
        aserder = serdering.SerderKERI(raw=anc)

        qviCred.issue(creder=creder, serder=iserder)
        qviRar.issue(creder=creder, iserder=iserder, anc=aserder)

        while not self.qviRgy.reger.saved.get(creder.said):
            self.qviRgy.processEscrows()
            qviRar.processEscrows()
            qviVer.processEscrows()
            qviCred.processEscrows()

        self.lesaid = creder.said
        assert self.lesaid == "EL5nGzlXb8DEjFh4pOZMd7F10NYfX7inyci3iw9juY6_"
        # Parse the Legal Entity credential and all its crypto goodness into Legal Entity
        parsing.Parser().parse(ims=share_credential(self.qviHab, self.qviRgy, creder.said),
                               kvy=leeKvy, tvy=leeVer.tvy, vry=leeVer)

        while not self.leeRgy.reger.saved.get(creder.said):
            leeKvy.processEscrows()
            self.leeRgy.processEscrows()
            leeVer.processEscrows()

        # Check to ensure the Legal Entity has the Legal Entity credential in database
        issd = self.leeRgy.reger.saved.get(creder.said)
        assert issd.qb64 == creder.said

        # Issue OOR AUTH Credential from LE to QVI
        # Create edges pointing back to LE credential
        edges = dict(d="", le=dict(n=creder.said, s=handling.LE_SCHEMA))
        _, edges = coring.Saider.saidify(sad=edges, label=coring.Saids.d)

        leeCred = credentialing.Credentialer(hby=self.leeHby, rgy=self.leeRgy, registrar=leeRar, verifier=leeVer)
        creder = leeCred.create(regname=self.leeRgy.name,
                                recp=self.qviHab.pre,
                                schema=handling.OOR_AUTH_SCHEMA,
                                source=edges,
                                rules=rules,
                                data=dict(
                                    AID=self.perHab.pre,
                                    LEI="5493001KJTIIGC8Y1R17",
                                    officialRole="Baba Yaga",
                                    personLegalName="John Wick"),
                                private=False)
        iserder = leeRegy.issue(said=creder.said)
        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])
        rseal = eventing.SealEvent(vcid, rseq.snh, iserder.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        anc = self.leeHab.interact(data=[rseal])
        aserder = serdering.SerderKERI(raw=anc)

        leeCred.issue(creder=creder, serder=iserder)
        leeRar.issue(creder=creder, iserder=iserder, anc=aserder)

        while not self.leeRgy.reger.saved.get(creder.said):
            self.leeRgy.processEscrows()
            leeRar.processEscrows()
            leeVer.processEscrows()
            leeCred.processEscrows()

        assert creder.said == "EM4Q5HNAiVZGqzPL1BJVGF0GCIUYng07kFIz49dC7n2c"
        # Parse the AUTH credential and all its crypto goodness into QVI
        parsing.Parser().parse(ims=share_credential(self.leeHab, self.leeRgy, creder.said),
                               kvy=qviKvy, tvy=qviVer.tvy, vry=qviVer)

        while not self.qviRgy.reger.saved.get(creder.said):
            qviKvy.processEscrows()
            self.qviRgy.processEscrows()
            qviVer.processEscrows()

        # Check to ensure the QVI has the AUTH credential in database
        issd = self.qviRgy.reger.saved.get(creder.said)
        assert issd.qb64 == creder.said

        # Issue OOR Credential from QVI to Person
        # Create edges pointing back to AUTH credential
        edges = dict(d="", auth=dict(n=creder.said, o="I2I", s=handling.OOR_AUTH_SCHEMA))
        _, edges = coring.Saider.saidify(sad=edges, label=coring.Saids.d)

        qviCred = credentialing.Credentialer(hby=self.qviHby, rgy=self.qviRgy, registrar=qviRar, verifier=qviVer)
        creder = qviCred.create(regname=self.qviRgy.name,
                                recp=self.perHab.pre,
                                schema=handling.OOR_SCHEMA,
                                source=edges,
                                rules=rules,
                                data=dict(
                                    LEI="5493001KJTIIGC8Y1R17",
                                    personLegalName="John Wick",
                                    officialRole="Baba Yaga"),
                                private=False)
        iserder = qviRegy.issue(said=creder.said)
        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])
        rseal = eventing.SealEvent(vcid, rseq.snh, iserder.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        anc = self.qviHab.interact(data=[rseal])
        aserder = serdering.SerderKERI(raw=anc)

        qviCred.issue(creder=creder, serder=iserder)
        qviRar.issue(creder=creder, iserder=iserder, anc=aserder)

        while not self.qviRgy.reger.saved.get(creder.said):
            self.qviRgy.processEscrows()
            qviRar.processEscrows()
            qviVer.processEscrows()
            qviCred.processEscrows()

        self.oorsaid = creder.said
        assert self.oorsaid == "EHZ05NsGCdWNujHTK3FqyuPmR8qz04Q3xg3Hnz1hkPmm"


def openHab(name, temp, salt):
    salt = coring.Salter(raw=salt).qb64

    hby = habbing.Habery(name=name, base="", temp=temp, salt=salt)
    hab = hby.makeHab(name=name, icount=1, isith='1', ncount=1, nsith='1')
    return hby, hab


def create_registry(hby, hab, rgy, salt):
    registrar = credentialing.Registrar(hby=hby, rgy=rgy, counselor=None)
    conf = dict(nonce=salt, estOnly=False, noBackers=True)
    registry = rgy.makeRegistry(name=hab.name, prefix=hab.pre, **conf)

    rseal = SealEvent(registry.regk, "0", registry.regd)
    rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)
    anc = hab.interact(data=[rseal])

    aserder = serdering.SerderKERI(raw=bytes(anc))
    registrar.incept(iserder=registry.vcp, anc=aserder)

    rgy.processEscrows()
    registrar.processEscrows()

    assert rgy.reger.ctel.get(keys=(registry.regk, coring.Seqner(sn=0).qb64)) is not None

    return registry, registrar


def share_credential(hab, rgy, said):
    msgs = bytearray()
    creder, prefixer, seqner, saider = rgy.reger.cloneCred(said=said)

    for msg in hab.db.clonePreIter(pre=creder.issuer):
        msgs.extend(msg)

    for msg in rgy.reger.clonePreIter(pre=creder.regi):
        msgs.extend(msg)

    for msg in rgy.reger.clonePreIter(pre=creder.said):
        msgs.extend(msg)

    chains = creder.edge or {}
    saids = []
    for key, source in chains.items():
        if key == 'd':
            continue

        if not isinstance(source, dict):
            continue

        saids.append(source['n'])

    for esaid in saids:
        msgs.extend(share_credential(hab, rgy, esaid))

    msgs.extend(creder.raw)
    msgs.extend(signing.serialize(creder, prefixer, seqner, saider))

    return bytes(msgs)
