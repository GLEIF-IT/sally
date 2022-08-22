# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.handling module

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
from keri import help, kering

logger = help.ogler.getLogger()

QVI_SCHEMA = "EWCeT9zTxaZkaC_3-amV2JtG6oUxNA36sCC0P5MI7Buw"
LE_SCHEMA = "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"
OOR_SCHEMA = "E2RzmSCFmG2a5U2OqZF-yUobeSYkW-a3FsN82eZXMxY0"


def loadHandlers(cdb, exc, tvy):
    """ Load handlers for the peer-to-peer challenge response protocol

    Parameters:
        cdb (CueBaser): communication escrow database environment
        exc (Exchanger): Peer-to-peer message router
        tvy (Tevery): transaction event log processor

    """
    proofs = PresentationProofHandler(cdb=cdb)
    exc.addHandler(proofs)


class PresentationProofHandler(doing.Doer):
    """ Processor for responding to presentation proof peer to peer message.

      The payload of the message is expected to have the following format:

    """

    resource = "/presentation"

    def __init__(self, cdb, cues=None, **kwa):
        """ Initialize instance

        Parameters:
            cdb (CueBaser): communication escrow database environment
            cue(Deck): outbound cues
            **kwa (dict): keyword arguments passes to super Doer

        """
        self.msgs = decking.Deck()
        self.cues = cues if cues is not None else decking.Deck()
        self.cdb = cdb

        super(PresentationProofHandler, self).__init__()

    def do(self, tymth, tock=0.0, **opts):
        """ Handle incoming messages by queueing presentation messages to be handled when credential is received

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Messages:
            payload is dict representing the body of a /presentation message
            pre is qb64 identifier prefix of sender


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

    def __init__(self, hby, hab, cdb, reger, auth, hook):
        """

        Create a communicator capable of persistent processing of messages and performing
        web hook calls.

        Parameters:
            hby (Habery): identifier database environment
            hab (Hab): identifier environment of this Communicator.  Used to sign hook calls
            cdb (CueBaser): communication escrow database environment
            reger (Reger): credential registry and database
            auth (str): AID of external authority for contacts and credentials
            hook (str): web hook to call in response to presentations and revocations

        """
        self.hby = hby
        self.hab = hab
        self.cdb = cdb
        self.reger = reger
        self.hook = hook
        self.auth = auth
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

                try:
                    regk = creder.status
                    state = self.reger.tevers[regk].vcState(creder.said)
                    if state is None or state.ked['et'] not in (coring.Ilks.iss, coring.Ilks.bis):
                        raise kering.ValidationError(f"revoked credential {creder.said} being presented")

                    if creder.schema == QVI_SCHEMA:
                        self.validateQualifiedvLEIIssuer(creder)
                    elif creder.schema == LE_SCHEMA:
                        self.validateLegalEntity(creder)
                    elif creder.schema == OOR_SCHEMA:
                        self.validateOfficialRole(creder)
                    else:
                        raise kering.ValidationError(f"credential {creder.said} is of unsupported schema"
                                                     f" {creder.schema} from issuer {creder.issuer}")
                except kering.ValidationError as ex:
                    logger.error(f"credential {creder.said} from issuer {creder.issuer} failed validation: {ex}")
                else:
                    self.cdb.recv.pin(keys=(said, dater.qb64), val=creder)
                finally:
                    self.cdb.iss.rem(keys=(said,))

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
                if action == "iss":  # presentation of issued credential
                    if creder.schema == QVI_SCHEMA:
                        data = self.entityPayload(creder)
                    elif creder.schema == LE_SCHEMA:
                        data = self.entityPayload(creder)
                    elif creder.schema == OOR_SCHEMA:
                        data = self.roleCredentialPayload(creder)
                    else:
                        raise kering.ValidationError("this will never happen because all credentials that get here are"
                                                     " valid")
                else:  # revocation of credential
                    data = self.revokePayload(creder)

                self.request(creder.said, resource, action, actor, data)
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
        for (said,), creder in self.cdb.ack.getItemIter():
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

    def validateQualifiedvLEIIssuer(self, creder):
        """ Validate issuer of QVI against known valid issuer

        Parameters:
            creder (Creder): QVI credential to validate

        Raises:
            ValidationError: If credential was not issued from known valid issuer

        """
        if creder.schema != QVI_SCHEMA:
            raise kering.ValidationError(f"invalid schema {creder.schema} for QVI credential {creder.said}")

        if not creder.issuer == self.auth:
            raise kering.ValidationError("QVI credential not issued by known valid issuer")

    def validateLegalEntity(self, creder):
        if creder.schema != LE_SCHEMA:
            raise kering.ValidationError(f"invalid schema {creder.schema} for LE credential {creder.said}")

        self.validateQVIChain(creder)

    def validateOfficialRole(self, creder):
        if creder.schema != OOR_SCHEMA:
            raise kering.ValidationError(f"invalid schema {creder.schema} for OOR credential {creder.said}")

        self.validateQVIChain(creder)

        edges = creder.crd["e"]
        lesaid = edges["le"]["n"]
        le = self.reger.creds.get(lesaid)
        if le is None:
            raise kering.ValidationError(f"LE credential {lesaid} not found for OOR credential {creder.said}")

        self.validateLegalEntity(le)

    def validateQVIChain(self, creder):
        edges = creder.crd["e"]
        qsaid = edges["qvi"]["n"]
        qcreder = self.reger.creds.get(qsaid)
        if qcreder is None:
            raise kering.ValidationError(f"QVI credential {qsaid} not found for credential {creder.said}")

        self.validateQualifiedvLEIIssuer(qcreder)

    @staticmethod
    def entityPayload(creder):
        a = creder.crd["a"]
        data = dict(
            schema=creder.schema,
            issuer=creder.issuer,
            issueTimestamp=a["dt"],
            credential=creder.said,
            recipient=a["i"],
            LEI=a["LEI"]
        )

        return data

    @staticmethod
    def roleCredentialPayload(creder):
        a = creder.crd["a"]
        data = dict(
            schema=creder.schema,
            issuer=creder.issuer,
            issueTimestamp=a["dt"],
            credential=creder.said,
            recipient=a["i"],
            LEI=a["LEI"],
            personLegalName=a["personLegalName"],
            officialRole=a["officialRole"]
        )

        return data

    def revokePayload(self, creder):
        regk = creder.status
        state = self.reger.tevers[regk].vcState(creder.said)

        data = dict(
            schema=creder.schema,
            credential=creder.said,
            revocationTimestamp=state.ked["dt"]
        )

        return data