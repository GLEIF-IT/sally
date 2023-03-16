# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.serving module

Endpoint service
"""
import json
from collections import namedtuple

import falcon
from base64 import urlsafe_b64encode as encodeB64

from hio import base
from hio.base import doing
from hio.core import http
from hio.help import decking
from keri import help
from keri.app import indirecting, storing
from keri.core import routing, eventing, coring
from keri.end import ending
from keri.peer import exchanging
from keri.vdr import viring, verifying
from keri.vdr.eventing import Tevery

from sally.core import handling, basing
from sally.core.handling import CredentialMapping

logger = help.ogler.getLogger()


def setup(hby, *, alias, httpPort, hook, auth, listen=False, timeout=10, retry=3, mappings=[]):
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
        mappings (list): mappings of credential types to schema SAIDs for selecting validation and handler functions
    """
    # make hab
    hab = hby.habByName(name=alias)
    if hab is None:
        hab = hby.makeHab(name=alias, transferable=True)

    print(f"Using hab {hab.name}:{hab.pre}")
    print(f"\tCESR Qualifed Base64 Public Key:  {hab.kever.serder.verfers[0].qb64}")
    print(f"\tPlain Base64 Public Key:          {encodeB64(hab.kever.serder.verfers[0].raw).decode('utf-8')}")
    mbx = storing.Mailboxer(name=hby.name)
    reger = viring.Reger(name=hab.name, db=hab.db, temp=False)
    rep = storing.Respondant(hby=hby, mbx=mbx)
    verifier = verifying.Verifier(hby=hby, reger=reger)
    cdb = basing.CueBaser(name=hby.name)
    comms = handling.Communicator(hby=hby,
                                  hab=hab,
                                  cdb=cdb,
                                  reger=reger,
                                  auth=auth,
                                  hook=hook,
                                  timeout=timeout,
                                  retry=retry,
                                  mappings=mappings)

    rvy = routing.Revery(db=hby.db)

    exc = exchanging.Exchanger(db=hby.db, handlers=[])
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

    handling.loadHandlers(exc=exc, cdb=cdb)

    app = falcon.App(
        middleware=falcon.CORSMiddleware(
            allow_origins='*',
            allow_credentials='*',
            expose_headers=['cesr-attachment', 'cesr-date', 'content-type']))

    server = http.Server(port=httpPort, app=app)
    httpServerDoer = http.ServerDoer(server=server)

    ending.loadEnds(app, hby=hby, default=hab.pre)

    app.add_route('/credential-mappings',
                  RegisterCredToPrefixMappingEnd(tymth=None, hby=hby, communicator=comms))

    doers = [httpServerDoer, comms, exc, tc]
    if listen:
        print("This is where we start HttpEnd instead of MailboxDirector")
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
        doers.append(mbd)

    return doers


# Maps a credential name (credential_type) to a self addressing identifier (SAID/said)



class RegisterCredToPrefixMappingEnd(base.Tymee):
    """
    ReST API for adding a credential type to prefix mapping
    """

    def __init__(self, hby, communicator, **kwa):
        """
        Parameters:
            hab (habbing.Hab):  instance of local habitat
            tymth (function): tymth for superclass (inherited)
        """
        super(RegisterCredToPrefixMappingEnd, self).__init__(**kwa)
        self.hby = hby
        self.communicator = communicator

    def on_get(self, req, rep):
        """
        Handles GET requests
        """
        message = "\nKERI Service Endpoints\n\n"
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "text/html"
        rep.text = message

    def on_put(self, req, rep):
        """
        Handles PUT requests
        """
        print('received request')
        body = req.get_media()
        mappings = read_mappings(body)
        print(f'mappings received {mappings}')
        rep.status = falcon.HTTP_200  # This is the default status
        rep.content_type = "text/plain"
        rep.text = f'Received {len(mappings)} mappings'
        self.communicator.mappings = mappings


def read_mappings(body: dict) -> list[CredentialMapping]:
    return [CredentialMapping(**k) for k in body["mappings"]]


class TeveryCuery(doing.Doer):

    def __init__(self, cdb, reger, cues=None, **kwa):

        self.cdb = cdb
        self.reger = reger
        self.cues = cues if cues is not None else decking.Deck()

        super(TeveryCuery, self).__init__(**kwa)

    def do(self, tymth, *, tock=0.0, **opts):
        """  Do override to process incoming challenge responses

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        """
        # start enter context
        self.wind(tymth)
        self.tock = tock
        yield self.tock

        while True:

            while self.cues:
                cue = self.cues.popleft()
                if cue['kin'] == "revoked":
                    serder = cue["serder"]
                    said = serder.ked["i"]
                    creder = self.reger.creds.get(said)
                    if creder is None:
                        logger.error(f"revocation received for unknown credential {said}")

                    prefixer = coring.Prefixer(qb64=creder.issuer)
                    saider = coring.Saider(qb64=said)
                    now = coring.Dater()

                    self.cdb.snd.pin(keys=(saider.qb64,), val=prefixer)
                    self.cdb.rev.pin(keys=(saider.qb64,), val=now)

                yield self.tock

            yield self.tock
