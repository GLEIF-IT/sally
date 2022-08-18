# -*- encoding: utf-8 -*-
"""
KARA
kara.core.handling module

EXN Message handling
"""
import datetime
import json
from urllib import parse

from hio.base import doing
from hio.core import http
from hio.help import decking, Hict
from keri.core import coring
from keri.end import ending
from keri.help import helping


def loadHandlers(hby, cdb, exc):
    """ Load handlers for the peer-to-peer challenge response protocol

    Parameters:
        hby (Habery): database environment
        cdb (CueBaser): communication escrow database environment
        exc (Exchanger): Peer-to-peer message router

    """
    proofs = PresentationProofHandler(hby=hby, cdb=cdb)
    exc.addHandler(proofs)


class PresentationProofHandler(doing.Doer):
    """ Processor for responding to presentation proof peer to peer message.

      The payload of the message is expected to have the following format:

    """

    resource = "/presentation"

    def __init__(self, hby, cdb, cues=None, **kwa):
        """ Initialize instance

        Parameters:
            hby (Habery): database environment
            cdb (CueBaser): communication escrow database environment
            cue(Deck): outbound cues
            **kwa (dict): keyword arguments passes to super Doer

        """
        self.msgs = decking.Deck()
        self.cues = cues if cues is not None else decking.Deck()
        self.hby = hby
        self.cdb = cdb

        super(PresentationProofHandler, self).__init__()

    def do(self, tymth, tock=0.0, **opts):
        """ Handle incoming messages by parsing and verifying the credential and storing it in the wallet

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Messages:
            payload is dict representing the body of a /credential/issue message
            pre is qb64 identifier prefix of sender
            sigers is list of Sigers representing the sigs on the /credential/issue message
            verfers is list of Verfers of the keys used to sign the message


        """
        self.wind(tymth)
        self.tock = tock
        yield self.tock

        while True:
            while self.msgs:
                msg = self.msgs.popleft()
                payload = msg["payload"]
                # TODO: limit presentations from issuee or issuer from flag.

                sender = payload["i"]
                said = payload["a"] if "a" in payload else payload["n"]

                prefixer = coring.Prefixer(qb64=sender)
                saider = coring.Saider(qb64=said)
                now = coring.Dater()

                self.cdb.snd.pin(keys=(saider.qb64,), val=prefixer)
                self.cdb.iss.pin(keys=(saider.qb64,), val=now)

                yield self.tock

            yield self.tock


class Communicator(doing.DoDoer):
    """
    Communicator is responsible for comminucating the receipt and successful verification
    of credential presentation and revocation messages from external third parties via
    web hook API calls.


    """

    TimeoutComms = 600

    def __init__(self, hby, hab, cdb, reger, hook):
        """

        Create a communicator capable of persistent processing of messages and performing
        web hook calls.

        Parameters:
            hby (Habery): identifier database environment
            hab (Hab): identifier environment of this Communicator.  Used to sign hook calls
            cdb (CueBaser): communication escrow database environment
            reger (Reger): credential registry and database
            hook (str): web hook to call in response to presentations and revocations

        """
        self.hby = hby
        self.hab = hab
        self.cdb = cdb
        self.reger = reger
        self.hook = hook
        self.clients = dict()

        super(Communicator, self).__init__(doers=[doing.doify(self.escrowDo)])

    def processPresentations(self):

        for (said,), dater in self.cdb.iss.getItemIter():

            # cancel presentations that have been around longer than timeout
            now = helping.nowUTC()
            if now - dater.datetime > datetime.timedelta(seconds=self.TimeoutComms):
                self.cdb.iss.rem(keys=(said,))
                continue

            if self.reger.saved.get(keys=(said,)) is not None:
                creder = self.reger.creds.get(keys=(said,))
                self.cdb.iss.rem(keys=(said,))
                self.cdb.recv.pin(keys=(said, dater.qb64), val=creder)

    def processRevocations(self):

        for (said,), dater in self.cdb.rev.getItemIter():

            # cancel revocations that have been around longer than timeout
            now = helping.nowUTC()
            if now - dater.datetime > datetime.timedelta(seconds=self.TimeoutComms):
                self.cdb.rev.rem(keys=(said,))
                continue

            creder = self.reger.ccrd.get(keys=(said,))
            if creder is None:  # received revocation before credential.  probably an error but let it timeout
                continue

            regk = creder.status
            state = self.reger.tevers[regk].vcState(creder.said)
            if state is None:  # received revocation before status.  probably an error but let it timeout
                continue

            elif state.ked['et'] in (coring.Ilks.iss, coring.Ilks.bis):  # haven't received revocation event yet
                continue

            elif state.ked['et'] in (coring.Ilks.rev, coring.Ilks.brv):  # revoked
                self.cdb.rev.rem(keys=(said,))
                self.cdb.revk.pin(keys=(said, dater.qb64), val=creder)

    def processReceived(self, db, action):

        for (said, dates), creder in db.getItemIter():
            if said not in self.clients:
                resource = creder.schema
                actor = creder.issuer
                # TODO: include revocation date with payload for revocation
                self.request(creder.said, resource, action, actor, creder.crd)
                continue

            (client, clientDoer) = self.clients[said]
            if client.responses:
                response = client.responses.popleft()
                self.remove([clientDoer])
                client.close()
                del self.clients[said]

                if response["status"] == 200:
                    db.rem(keys=(said, dates))
                    self.cdb.ack.pin(keys=(said,), val=creder)
                else:
                    dater = coring.Dater(qb64=dates)
                    now = helping.nowUTC()
                    if now - dater.datetime > datetime.timedelta(seconds=self.TimeoutComms):
                        db.rem(keys=(said, dates))

    def processAcks(self):
        for (said, ), creder in self.cdb.ack.getItemIter():
            # TODO: generate EXN ack message with credential information
            print(f"ACK for credential {said} will be sent to {creder.issuer}")
            self.cdb.ack.rem(keys=(said,))

    def escrowDo(self, tymth, tock=1.0):
        """ Process escrows of comms pipeline

        Steps involve:
           1. Sending local event with sig to other participants
           2. Waiting for signature threshold to be met.
           3. If elected and delegated identifier, send complete event to delegator
           4. If delegated, wait for delegator's anchor
           5. If elected, send event to witnesses and collect receipts.
           6. Otherwise, wait for fully receipted event

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value.  Default to 1.0 to slow down processing

        """
        # enter context
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            try:
                self.processEscrows()
            except Exception as e:
                print(e)

            yield 0.5

    def processEscrows(self):
        """
        Process communication pipelines

        """
        self.processPresentations()
        self.processRevocations()
        self.processReceived(db=self.cdb.recv, action="iss")
        self.processReceived(db=self.cdb.revk, action="rev")
        self.processAcks()

    def request(self, said, resource, action, actor, data):
        """ Generate and launch request to remote hook

        Parameters:
            said (str): qb64 SAID of credential
            data (dict): serializable body to send with call
            action (str): the action performed on he resource [iss|rev]
            actor (str): qualified b64 AID of sender of the event
            resource (str): the resource type that triggered the event

        """
        purl = parse.urlparse(self.hook)
        client = http.clienting.Client(hostname=purl.hostname, port=purl.port)
        clientDoer = http.clienting.ClientDoer(client=client)
        self.extend([clientDoer])

        body = dict(
            action=action,
            actor=actor,
            data=data
        )

        raw = json.dumps(body).encode("utf-8")
        sigers = self.hab.sign(ser=raw,
                               verfers=self.hab.kever.verfers,
                               indexed=True)

        signage = ending.Signage(markers=sigers, indexed=True, signer=None, ordinal=None, digest=None,
                                 kind=None)

        headers = Hict([
            ("Content-Type", "application/json"),
            ("Content-Length", len(raw)),
            ("Connection", "close"),
            ("Sally-Resource", resource),
            ("Sally-Timestamp", helping.nowIso8601()),
        ])

        headers.extend(ending.signature([signage]))

        path = purl.path or "/"
        client.request(
            method='POST',
            path=path,
            qargs=parse.parse_qs(purl.query),
            headers=headers,
            body=raw
        )

        self.clients[said] = (client, clientDoer)
