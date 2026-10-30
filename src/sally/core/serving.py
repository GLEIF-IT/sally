# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.serving module

Endpoint service
"""
import os
from typing import List

import falcon
from base64 import urlsafe_b64encode as encodeB64

from hio.base import doing, Doer
from hio.core import http
from hio.help import decking
from keri.app import indirecting, storing, notifying, habbing, oobiing
from keri.app.cli.commands import incept
from keri.app.habbing import Habery, Hab
from keri.core import routing, eventing, parsing
from keri.end import ending
from keri.peer import exchanging
from keri.vdr import viring, verifying
from keri.vdr.eventing import Tevery
from keri.vc import protocoling

from sally import ogler, log_name
from sally.core import handling, basing, monitoring, httping, metrics as metricsmod, scheduling, configing
from sally.core.credentials import TeveryCuery
from sally.core.verifying import VerificationAgent

logger = ogler.getLogger(log_name)

def incept_if_new(hby: Habery, alias: str, incept_args: dict):
    """
    Create an identifier with the specified alias if it does not exist.
    This is run in a separate scheduler (Doist) prior to starting Sally so that the identifier can
    exist and have all Habery configuration OOBIs resolved.

    Warning: This only supports no witness, single sig identifiers as it is assumed it will be used
        with the direct-mode verification agent.
    """
    if incept_args is None:
        incept_args = {}
    hab = hby.habByName(name=alias)
    if hab is None:
        # Incept the new Hab
        if incept_args["incept_file"] is None:
            raise ValueError("incept file by arg --incept-file is required to create a new identifier")
        logger.info(f"Making new hab {alias} in Habery {incept_args.get('name', '')}")
        hab = hby.makeHab(name=alias, **inception_config(**incept_args))
    else:
        logger.info(f"Hab '{alias}' already exists, using...")
    return hab

def run_doers(doers: List[Doer], expire=0.0, *, tock=None):
    """Runs the verifier in a Doist until the specified expire time (in seconds)."""
    tock = scheduling.resolveTocks()["root"] if tock is None else configing.validateDuration(tock, "root tock", positive=True)
    doist = doing.Doist(limit=expire, tock=tock, real=True)
    doist.do(doers=doers)


def setupDoers(
        hby: Habery, hab: Hab, alias: str, http_port: int, hook: str, auth: str,
        timeout: float = None, retry: float = None, direct: bool = True,
        incept_args: dict = None, tocks=None, verifier_config=None):
    """
    Parameters:
        hby (Habery): identifier database environment
        alias (str): alias of the identifier representing this agent
        httpPort (int): external port to listen on for HTTP messages
        hook (str): URL of external web hook to notify of credential issuance and revocations
        auth (str): alias or AID of external authority for contacts and credentials
        timeout (float): escrow timeout (in seconds) for events not delivered to upstream web hook
        retry (float): retry delay (in seconds) for failed web hook attempts
        direct (bool): listen for direct-mode messages on HTTP port or use indirect-mode mailbox
        incept_args (dict): arguments for incepting Sally's identifier if it does not exist
        tocks (dict): already resolved coroutine cadences in seconds
        verifier_config (VerifierConfig): already resolved retry/deadline settings in seconds
    """
    tocks = scheduling.loadTocks(hby.cf) if tocks is None else tocks
    if verifier_config is None:
        verifier_config = configing.loadVerifierConfig(hby.cf, retry=retry, timeout=timeout)
    hbyDoer = habbing.HaberyDoer(habery=hby)
    obl = oobiing.Oobiery(hby=hby)

    doers = [hbyDoer, *obl.doers]
    doers += setup(hby, hab, alias=alias, httpPort=http_port, hook=hook, auth=auth, timeout=timeout,
                   retry=retry, direct=direct, tocks=tocks, verifier_config=verifier_config)
    return doers

def setup(hby: Habery, hab: Hab, alias: str, httpPort: int, hook: str, auth: str, timeout=None,
          retry=None, direct=True, tocks=None, verifier_config=None):
    """
    Setup components, HTTP endpoints, and MailboxDirector working with witnesses to receive events.

    Parameters:
        hby (Habery): identifier database environment
        alias (str): alias of the identifier representing this agent
        httpPort (int): external port to listen on for HTTP messages
        hook (str): URL of external web hook to notify of credential issuance and revocations
        auth (str): alias or AID of external authority for contacts and credentials
        timeout (float): escrow timeout (in seconds) for events not delivered to upstream web hook
        retry (float): retry delay (in seconds) for failed web hook attempts
        direct (bool): listen for direct-mode messages on HTTP port or use indirect-mode mailbox
        tocks (dict): already resolved coroutine cadences in seconds
        verifier_config (VerifierConfig): already resolved retry/deadline settings in seconds
    """
    tocks = scheduling.loadTocks(hby.cf) if tocks is None else tocks
    if verifier_config is None:
        verifier_config = configing.loadVerifierConfig(hby.cf, retry=retry, timeout=timeout)
    cues = decking.Deck()
    if hab is None:
        raise ValueError(f"Identifier with alias '{alias}' does not exist. It must be created before starting Sally.")

    logger.info(f"Using hab {hab.name}:{hab.pre}")
    logger.info(f"\tCESR Qualifed Base64 Public Key:  {hab.kever.serder.verfers[0].qb64}")
    logger.info(f"\tPlain Base64 Public Key:          {encodeB64(hab.kever.serder.verfers[0].raw).decode('utf-8')}")

    # HTTP Server
    app = falcon.App(middleware=httping.cors_middleware())
    metrics = metricsmod.Metrics()
    server = http.Server(port=httpPort, app=app)
    httpServerDoer = http.ServerDoer(server=server, tock=tocks["httpServer"])

    # KEL, ACDC, exchange message, and reply message components
    reger = viring.Reger(name=hab.name, db=hab.db, temp=False)
    verifier = verifying.Verifier(hby=hby, reger=reger)

    mbx = storing.Mailboxer(name=hby.name)
    exc = exchanging.Exchanger(hby=hby, handlers=[])
    rep = storing.Respondant(hby=hby, mbx=mbx)

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
    tc = TeveryCuery(cdb=cdb, reger=reger, cues=tvy.cues, metrics=metrics, tock=tocks["revocation"])

    parser = parsing.Parser(
        framed=True,
        kvy=kvy,
        tvy=tvy,
        rvy=rvy,
        vry=verifier,
        exc=exc,
    )

    comms = handling.Communicator(
        hby=hby, hab=hab, cdb=cdb, reger=reger, auth=auth, hook=hook,
        timeout=verifier_config.escrow_timeout_seconds,
        retry=verifier_config.retry_delay_seconds,
        metrics=metrics,
        escrow_tock=tocks["communicatorEscrow"],
        client_tock=tocks["webhookClient"],
        tock=tocks["communicator"],
        request_timeout=verifier_config.webhook_request_timeout_seconds,
    )
    app.add_route("/health", monitoring.HealthEnd(cdb=cdb))
    app.add_route("/metrics", monitoring.MetricsEnd(metrics=metrics, db=hby.db, reger=reger, cdb=cdb))

    ending.loadEnds(app, hby=hby, default=hab.pre)

    doers: List[Doer] = [httpServerDoer, comms, tc]
    if direct:
        logger.info("Adding direct mode HTTP listener")
        # reading notifications for received ipex grant exn messages
        doers.extend(
            handling.loadHandlers(
                cdb=cdb,
                hby=hby,
                notifier=notifier,
                parser=parser,
                metrics=metrics,
                tock=tocks["presentation"],
            )
        )

        # Set up HTTP endpoint for PUT-ing application/cesr streams to the SallyAgent at '/'
        httpEnd = indirecting.HttpEnd(rxbs=parser.ims, mbx=mbx)
        app.add_route('/', httpEnd)
        agent = VerificationAgent(hab=hab, parser=parser, kvy=kvy, tvy=tvy, rvy=rvy, verifier=verifier, exc=exc, cues=cues,
                                  tock=tocks["verifier"], msg_tock=tocks["verifierMsg"],
                                  escrow_tock=tocks["verifierEscrow"])
        doers.append(agent)
    else:
        logger.info("Adding indirect mode mailbox listener")
        mbd = indirecting.MailboxDirector(
            hby=hby, exc=exc, kvy=kvy, tvy=tvy, rvy=rvy, verifier=verifier, rep=rep,
            topics=["/receipt", "/replay", "/multisig", "/credential", "/delegate", "/challenge"])  # topics to listen for messages on
        # reading notifications for received ipex grant exn messages
        doers.extend(
            handling.loadHandlers(
                cdb=cdb,
                hby=hby,
                notifier=notifier,
                parser=mbd.parser,
                metrics=metrics,
                tock=tocks["presentation"],
            )
        )
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

def inception_config(name=None, base=None, alias=None, bran=None, incept_file=None, config_dir=None):
    """
    Inception configuration for Sally's identifier prefix.
    Returns a dict of inception arguments for Sally's identifier prefix.

    This uses an object so that it can be merged with the incept file configuration like the
    multicommand args object by using object properties rather than dictionary keys, which is what
    incept.mergeArgsWithFile expects.
    """
    class Object(object):
        pass
    icp_args = Object()
    icp_args.name = name
    icp_args.base = base
    icp_args.alias = alias
    icp_args.bran = bran
    icp_args.file = incept_file if config_dir is None else os.path.join(config_dir, incept_file)
    icp_args.transferable = True
    icp_args.icount = None
    icp_args.wits = []
    icp_args.toad = None
    icp_args.isith = None
    icp_args.ncount = None
    icp_args.nsith = None
    icp_args.delpre = None
    icp_args.est_only = False
    icp_args.data = None
    return incept.mergeArgsWithFile(icp_args).__dict__
