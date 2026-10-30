"""Temporary KERI state for exercising the verifier's real processing pipeline."""
from contextlib import contextmanager
from dataclasses import dataclass

import pytest
from hio.base import doing
from keri.app import habbing
from keri.core import coring, eventing, parsing, routing, serdering
from keri.db import dbing
from keri.peer import exchanging
from keri.vc import proving
from keri.vdr import credentialing, verifying, viring
from keri.vdr import eventing as veventing

from sally.core import basing, handling
from sally.core.verifying import VerificationAgent


@dataclass(frozen=True)
class VerificationContext:
    """Connected real processors sharing one temporary identifier and credential store."""

    hby: habbing.Habery
    hab: habbing.Hab
    reger: viring.Reger
    rvy: routing.Revery
    kvy: eventing.Kevery
    tvy: veventing.Tevery
    verifier: verifying.Verifier
    exc: exchanging.Exchanger
    parser: parsing.Parser


@pytest.fixture
def open_verification_context():
    """Own temporary Habery/Reger resources; leave schemas and handlers to the test."""
    @contextmanager
    def open_context(*, name='sally', base='', salt=None, expiry=None):
        """Accept raw salt bytes; optionally override KERIpy's ACDC expiry in seconds."""
        with (habbing.openHab(name=name, base=base, salt=salt, temp=True) as (hby, hab),
              dbing.openLMDB(cls=viring.Reger, name=name, db=hby.db, temp=True) as reger):
            rvy = routing.Revery(db=hby.db)
            kvy = eventing.Kevery(db=hby.db, rvy=rvy)
            tvy = veventing.Tevery(db=hby.db, reger=reger)
            kvy.registerReplyRoutes(router=rvy.rtr)
            tvy.registerReplyRoutes(router=rvy.rtr)
            verifier_options = {'expiry': expiry} if expiry is not None else {}
            verifier = verifying.Verifier(hby=hby, reger=reger, **verifier_options)
            exc = exchanging.Exchanger(hby=hby, handlers=[])
            parser = parsing.Parser(kvy=kvy, tvy=tvy, rvy=rvy, vry=verifier, exc=exc)
            yield VerificationContext(
                hby=hby, hab=hab, reger=reger, rvy=rvy, kvy=kvy, tvy=tvy,
                verifier=verifier, exc=exc, parser=parser,
            )

    return open_context


@pytest.fixture
def open_verification_agent(open_verification_context):
    """Add the real agent to a verification context and close its child doers on exit."""
    @contextmanager
    def open_agent(*, tock=0, msg_tock=0, escrow_tock=0, **context_options):
        with open_verification_context(**context_options) as context:
            agent = VerificationAgent(
                hab=context.hab,
                parser=context.parser,
                kvy=context.kvy,
                tvy=context.tvy,
                rvy=context.rvy,
                verifier=context.verifier,
                exc=context.exc,
                tock=tock,
                msg_tock=msg_tock,
                escrow_tock=escrow_tock,
            )
            try:
                yield agent
            finally:
                agent.exit()

    return open_agent


@pytest.fixture
def geda_qvi():
    """Create single-signature GEDA/QVI habitats and anchor GEDA's delegation approval."""
    with habbing.openHby(name='geda-qvi') as hby:
        geda = hby.makeHab(name='geda', icount=1, isith='1', ncount=1, nsith='1')
        qvi = hby.makeHab(name='qvi', delpre=geda.pre, icount=1, isith='1', ncount=1, nsith='1')
        inception = qvi.kever.serder

        # The QVI's local inception alone does not establish delegator approval.
        approval = serdering.SerderKERI(raw=geda.interact(data=[{
            'i': inception.pre,
            's': inception.snh,
            'd': inception.said,
        }]))
        # Include the authorizer event couple when replaying the QVI's KEL to Sally.
        hby.db.setAes(
            dbing.dgKey(inception.preb, inception.saidb),
            coring.Seqner(sn=approval.sn).qb64b + approval.saidb,
        )
        yield hby, geda, qvi


@pytest.fixture
def qvi_credential(geda_qvi, seeder):
    """Issue and verify a QVI ACDC from GEDA, with a real registry and KEL/TEL anchors."""
    hby, geda, qvi = geda_qvi
    seeder.load_schema(hby.db)
    with dbing.openLMDB(cls=viring.Reger, name='geda', temp=True) as reger:
        rgy = credentialing.Regery(hby=hby, reger=reger, temp=True)
        registry = rgy.makeRegistry(name='geda', prefix=geda.pre, noBackers=True)

        def anchor_tel_event(event):
            """GEDA signs the KEL seal, then the registry processes its pending TEL event."""
            anchor = serdering.SerderKERI(raw=geda.interact(data=[{
                'i': event.pre,
                's': event.snh,
                'd': event.said,
            }]))
            registry.anchorMsg(
                pre=event.pre,
                regd=event.said,
                seqner=coring.Seqner(sn=anchor.sn),
                saider=coring.Saider(qb64=anchor.said),
            )
            rgy.processEscrows()

        anchor_tel_event(registry.vcp)
        credential = proving.credential(
            schema=handling.QVI_SCHEMA,
            issuer=geda.pre,
            recipient=qvi.pre,
            status=registry.regk,
            data={'LEI': '254900OPPU84GM83MG36'},
        )
        issuance = registry.issue(said=credential.said)
        anchor_tel_event(issuance)
        verifier = verifying.Verifier(hby=hby, reger=reger)
        verifier.processCredential(
            creder=credential,
            prefixer=coring.Prefixer(qb64=issuance.pre),
            seqner=coring.Seqner(sn=issuance.sn),
            saider=coring.Saider(qb64=issuance.said),
        )
        assert reger.saved.get(keys=(credential.said,)) is not None
        yield credential


@pytest.fixture
def open_communicator(geda_qvi, qvi_credential):
    """Open Sally's communicator independently of the delegated QVI and its issuer."""
    authority, geda, qvi = geda_qvi

    @contextmanager
    def open_context(**options):
        with (habbing.openHby(name='sally') as hby,
              dbing.openLMDB(cls=basing.CueBaser, name='sally', temp=True) as cdb,
              dbing.openLMDB(cls=viring.Reger, name='sally', temp=True) as reger):
            sally = hby.makeHab(name='sally')
            parser = parsing.Parser(kvy=eventing.Kevery(db=hby.db, local=False))
            for hab in (geda, qvi):
                parser.parse(ims=bytearray().join(authority.db.clonePreIter(pre=hab.pre)))
            assert hby.kevers[qvi.pre].delpre == geda.pre
            comm = handling.Communicator(
                hby=hby, hab=sally, cdb=cdb, reger=reger, auth=geda.pre,
                hook=options.pop('hook', 'http://127.0.0.1:1/'), **options,
            )
            comm.wind(doing.Doist().tymen())
            try:
                # Keep Sally's credential store empty so pending-intake tests can
                # exercise the interval before the already-issued ACDC arrives.
                yield comm, qvi_credential
            finally:
                comm.exit()

    return open_context
