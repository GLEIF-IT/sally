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
from hio.help import decking
from keri import help
from keri.app import indirecting, storing, notifying
from keri.app.cli.commands import incept
from keri.core import routing, eventing
from keri.end import ending
from keri.peer import exchanging
from keri.vdr import viring, verifying
from keri.vdr.eventing import Tevery
from keri.vc import protocoling

from sally.core import handling, basing, monitoring, httping
from sally.core.credentials import TeveryCuery

logger = help.ogler.getLogger()

def setup(hby, *, alias, httpPort, hook, auth, timeout=10, retry=3, incept_args=None):
    """
    Setup components, HTTP endpoints, and MailboxDirector working with witnesses to receive events.

    Parameters:
        hby (Habery): identifier database environment
        alias (str): alias of the identifier representing this agent
        httpPort (int): external port to listen on for HTTP messages
        hook (str): URL of external web hook to notify of credential issuance and revocations
        auth (str): alias or AID of external authority for contacts and credentials
        timeout (int): escrow timeout (in minutes) for events not delivered to upstream web hook
        retry (int): retry delay (in seconds) for failed web hook attempts
        incept_args (dict): arguments for incepting Sally's identifier if it does not exist
    """
    # make hab
    if incept_args is None:
        incept_args = {}
    hab = hby.habByName(name=alias)
    if hab is None:
        logger.info(f"Making new hab {alias} in Habery {incept_args.get('name', '')}")
        hab = hby.makeHab(name=alias, **incept_args)

    logger.info(f"Using hab {hab.name}:{hab.pre}")
    logger.info(f"\tCESR Qualifed Base64 Public Key:  {hab.kever.serder.verfers[0].qb64}")
    logger.info(f"\tPlain Base64 Public Key:          {encodeB64(hab.kever.serder.verfers[0].raw).decode('utf-8')}")

    # HTTP Server
    app = falcon.App(middleware=httping.cors_middleware())
    server = http.Server(port=httpPort, app=app)
    httpServerDoer = http.ServerDoer(server=server)

    # KEL, ACDC, exchange message, and reply message components
    reger = viring.Reger(name=hab.name, db=hab.db, temp=False)
    verifier = verifying.Verifier(hby=hby, reger=reger)

    mbx = storing.Mailboxer(name=hby.name)
    exc = exchanging.Exchanger(hby=hby, handlers=[])

    cdb = basing.CueBaser(name=hby.name)
    clear_escrows(cdb)

    rvy = routing.Revery(db=hby.db)
    notifier = notifying.Notifier(hby=hby)
    # writes notifications for received IPEX grant exn messages
    protocoling.loadHandlers(hby=hby, exc=exc, notifier=notifier)

    kvy = eventing.Kevery(db=hby.db, lax=True, local=False, rvy=rvy)
    kvy.registerReplyRoutes(router=rvy.rtr)

    tvy = Tevery(reger=verifier.reger, db=hby.db, local=False)
    tvy.registerReplyRoutes(router=rvy.rtr)
    tc = TeveryCuery(cdb=cdb, reger=reger, cues=tvy.cues)

    comms = handling.Communicator(hby=hby, hab=hab, cdb=cdb, reger=reger,
                                  auth=auth, hook=hook, timeout=timeout, retry=retry)
    app.add_route("/health", monitoring.HealthEnd(cdb=cdb))

    ending.loadEnds(app, hby=hby, default=hab.pre)

    rep = storing.Respondant(hby=hby, mbx=mbx)
    mbd = indirecting.MailboxDirector(
        hby=hby, exc=exc, kvy=kvy, tvy=tvy, rvy=rvy, verifier=verifier, rep=rep,
        topics=["/receipt", "/replay", "/multisig", "/credential", "/delegate", "/challenge"])  # topics to listen for messages on

    doers = [httpServerDoer, comms, tc]
    # reading notifications for received ipex grant exn messages
    doers.extend(handling.loadHandlers(cdb=cdb, hby=hby, notifier=notifier, parser=mbd.parser))
    doers.append(mbd)

    return doers


def clear_escrows(cdb):
    """Clear escrows if the environment variable CLEAR_ESCROWS is set to True."""
    if env_var_to_bool("CLEAR_ESCROWS", True):
        logger.info("Clearing escrows")
        cdb.clearEscrows()


def env_var_to_bool(var_name, default=False):
    """Convert an environment variable to a boolean value."""
    val = os.getenv(var_name, default)
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ["true", "1"]
    return default

