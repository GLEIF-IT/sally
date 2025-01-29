# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.serving module

Endpoint service
"""
import os

import falcon
from base64 import urlsafe_b64encode as encodeB64

from hio.core import http
from keri import help
from keri.app import indirecting, storing, notifying
from keri.core import routing, eventing
from keri.end import ending
from keri.peer import exchanging
from keri.vdr import viring, verifying
from keri.vdr.eventing import Tevery
from keri.vc import protocoling

from sally.core import handling, basing
from sally.core.credentials import TeveryCuery

logger = help.ogler.getLogger()


def setup(hby, *, alias, httpPort, hook, auth, listen=False, timeout=10, retry=3):
    """ Setup serving package and endpoints

    Parameters:
        hby (Habery): identifier database environment
        alias (str): alias of the identifier representing this agent
        httpPort (int): external port to listen on for HTTP messages
        hook (str): URL of external web hook to notify of credential issuance and revocations
        auth (str): alias or AID of external authority for contacts and credentials
        listen (bool): flag indicating whether the agent listens persistently or polls mailboxes
        timeout (int): escrow timeout (in minutes) for events not delivered to upstream web hook
        retry (int): retry delay (in seconds) for failed web hook attempts

    """
    # make hab
    hab = hby.habByName(name=alias)
    if hab is None:
        hab = hby.makeHab(name=alias, transferable=True)

    logger.info(f"Using hab {hab.name}:{hab.pre}")
    logger.info(f"\tCESR Qualifed Base64 Public Key:  {hab.kever.serder.verfers[0].qb64}")
    logger.info(f"\tPlain Base64 Public Key:          {encodeB64(hab.kever.serder.verfers[0].raw).decode('utf-8')}")
    mbx = storing.Mailboxer(name=hby.name)
    reger = viring.Reger(name=hab.name, db=hab.db, temp=False)
    rep = storing.Respondant(hby=hby, mbx=mbx)
    verifier = verifying.Verifier(hby=hby, reger=reger)

    cdb = basing.CueBaser(name=hby.name)
    if env_var_to_bool("CLEAR_ESCROWS", True):
        logger.info("Clearing escrows")
        cdb.clearEscrows()

    comms = handling.Communicator(hby=hby,
                                  hab=hab,
                                  cdb=cdb,
                                  reger=reger,
                                  auth=auth,
                                  hook=hook,
                                  timeout=timeout,
                                  retry=retry)

    rvy = routing.Revery(db=hby.db)

    exc = exchanging.Exchanger(hby=hby, handlers=[])
    notifier = notifying.Notifier(hby=hby)
    # writes notifications for received IPEX grant exn messages
    protocoling.loadHandlers(hby=hby, exc=exc, notifier=notifier)
    kvy = eventing.Kevery(db=hby.db,
                          lax=True,
                          local=False,
                          rvy=rvy)
    kvy.registerReplyRoutes(router=rvy.rtr)

    tvy = Tevery(reger=verifier.reger,
                 db=hby.db,
                 local=False)
    tvy.registerReplyRoutes(router=rvy.rtr)
    tc = TeveryCuery(cdb=cdb, reger=reger, cues=tvy.cues)

    app = falcon.App(
        middleware=falcon.CORSMiddleware(
            allow_origins='*',
            allow_credentials='*',
            expose_headers=['cesr-attachment', 'cesr-date', 'content-type']))

    server = http.Server(port=httpPort, app=app)
    httpServerDoer = http.ServerDoer(server=server)

    ending.loadEnds(app, hby=hby, default=hab.pre)

    doers = [httpServerDoer, comms, tc]
    if listen:
        logger.info("This is where we start HttpEnd instead of MailboxDirector")
    else:
        mbd = indirecting.MailboxDirector(hby=hby,
                                          exc=exc,
                                          kvy=kvy,
                                          tvy=tvy,
                                          rvy=rvy,
                                          verifier=verifier,
                                          rep=rep,
                                          topics=["/receipt", "/replay", "/multisig", "/credential", "/delegate",
                                                  "/challenge"])
        # reading notifications for received ipex grant exn messages
        doers.extend(handling.loadHandlers(cdb=cdb, hby=hby, notifier=notifier, parser=mbd.parser))
        doers.append(mbd)

    return doers

def env_var_to_bool(var_name, default=False):
    val = os.getenv(var_name, default)
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ["true", "1"]
    return default

