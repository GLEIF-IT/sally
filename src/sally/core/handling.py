# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.handling module

EXN Message handling
"""
import datetime
import json
from base64 import urlsafe_b64encode as encodeB64
from collections import namedtuple
from urllib import parse

from hio.base import doing
from hio.core import http
from hio.help import decking, Hict
from keri import help, kering
from keri.core import coring
from keri.end import ending
from keri.help import helping

from sally.core import httping

logger = help.ogler.getLogger()
QVI_SCHEMA = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
LE_SCHEMA = "ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY"
OOR_AUTH_SCHEMA = "EKA57bKBKxr_kN7iN5i7lMUxpMG-s19dRcmov1iDxz-E"
OOR_SCHEMA = "EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy"

CredentialMapping = namedtuple('CredentialMapping', 'credential_type said')

def loadHandlers(cdb, exc):
    """ Load handlers for the peer-to-peer challenge response protocol

    Parameters:
        cdb (CueBaser): communication escrow database environment
        exc (Exchanger): Peer-to-peer message router

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


JOURNEY_TYPE = 'TreasureHuntingJourney'
REQUEST_TYPE = 'JourneyMarkRequest'
MARK_TYPE = 'JourneyMark'
CHARTER_TYPE = 'JourneyCharter'


class Communicator(doing.DoDoer):
    """
    Communicator is responsible for communicating the receipt and successful verification
    of credential presentation and revocation messages from external third parties via
    web hook API calls.


    """

    def __init__(self, hby, hab, cdb, reger, auth, hook, timeout=10, retry=3.0, mappings=[]):
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
            timeout (int): escrow timeout (in minutes) for events not delivered to upstream web hook
            retry (float): retry delay (in seconds) for failed web hook attempts

        """
        self.hby = hby
        self.hab = hab
        self.cdb = cdb
        self.reger = reger
        self.hook = hook
        self.auth = auth
        self.timeout = timeout
        self.retry = retry
        self.clients = dict()
        self.mappings: list[CredentialMapping] = mappings
        for mapping in self.mappings:
            print(f'Configured mapping of | {mapping.said} | {mapping.credential_type}')
        self.schema_handlers: dict = {
            JOURNEY_TYPE: self.validateJourney,
            REQUEST_TYPE: self.validateJourneyMarkRequest,
            MARK_TYPE: self.validateJourneyMark,
            CHARTER_TYPE: self.validateJourneyCharter,
            'QualifiedvLEIIssuervLEICredential': self.validateQVIChain,
            'LegalEntityvLEICredential': self.validateLegalEntity,
            'LegalEntityOfficialOrganizationalRolevLEICredential': self.validateOfficialRole
        }
        self.payload_handlers: dict = {
            JOURNEY_TYPE: self.treasureHuntingJourneyPayload,
            REQUEST_TYPE: self.journeyMarkRequestPayload,
            MARK_TYPE: self.journeyMarkPayload,
            CHARTER_TYPE: self.journeyCharterPayload,
            'QualifiedvLEIIssuervLEICredential': self.qviPayload,
            'LegalEntityvLEICredential': self.entityPayload,
            'LegalEntityOfficialOrganizationalRolevLEICredential': self.roleCredentialPayload
        }

        super(Communicator, self).__init__(doers=[doing.doify(self.escrowDo)])

    def processPresentations(self):

        for (said,), dater in self.cdb.iss.getItemIter():
            # cancel presentations that have been around longer than timeout
            now = helping.nowUTC()
            print(f"looking for credential {said}")
            if now - dater.datetime > datetime.timedelta(minutes=self.timeout):
                self.cdb.iss.rem(keys=(said,))
                continue

            if self.reger.saved.get(keys=(said,)) is not None:
                creder = self.reger.creds.get(keys=(said,))
                try:
                    regk = creder.status
                    state = self.reger.tevers[regk].vcState(creder.said)
                    if state is None or state.ked['et'] not in (coring.Ilks.iss, coring.Ilks.bis):
                        self.cdb.recv.pin(keys=(said, dater.qb64), val=creder)
                        raise kering.ValidationError(f"revoked credential {creder.said} being presented")

                    handler_type = self.resolve_said_to_type(creder.schema)
                    if handler_type in self.schema_handlers.keys():
                        handler = self.schema_handlers[handler_type]
                        handler(creder)
                    else:
                        raise kering.ValidationError(f"credential {creder.said} is of unsupported schema"
                                                     f" {creder.schema} from issuer {creder.issuer}")

                except kering.ValidationError as ex:
                    print(ex)
                    logger.error(f"credential {creder.said} from issuer {creder.issuer} failed validation: {ex}")
                else:
                    self.cdb.recv.pin(keys=(said, dater.qb64), val=creder)
                finally:
                    self.cdb.iss.rem(keys=(said,))

    def resolve_said_to_type(self, schema_said):
        for mapping in self.mappings:
            if mapping.said == schema_said:
                return mapping.credential_type
        raise kering.ValidationError(f"no mapping found for schema {schema_said}")

    def resolve_type_to_said(self, credential_type):
        for mapping in self.mappings:
            if mapping.credential_type == credential_type:
                return mapping.said
        raise kering.ValidationError(f"no mapping found for schema {credential_type}")

    def processRevocations(self):

        for (said,), dater in self.cdb.rev.getItemIter():

            # cancel revocations that have been around longer than timeout
            now = helping.nowUTC()
            if now - dater.datetime > datetime.timedelta(minutes=self.timeout):
                self.cdb.rev.rem(keys=(said,))
                continue

            creder = self.reger.creds.get(keys=(said,))
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
                    handler_type = self.resolve_said_to_type(creder.schema)
                    if handler_type in self.payload_handlers.keys():
                        handler = self.payload_handlers[handler_type]
                        data = handler(creder, self.reger)
                    else:
                        raise kering.ValidationError(f"credential {creder.said} is of unsupported schema"
                                                     f" {creder.schema} from issuer {creder.issuer}")
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

                if 200 <= response["status"] < 300:
                    db.rem(keys=(said, dates))
                    self.cdb.ack.pin(keys=(said,), val=creder)
                else:
                    dater = coring.Dater(qb64=dates)
                    now = helping.nowUTC()
                    if now - dater.datetime > datetime.timedelta(minutes=self.timeout):
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

            yield self.retry

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
        headers = Hict([
            ("Content-Type", "application/json"),
            ("Content-Length", len(raw)),
            ("Connection", "close"),
            ("Sally-Resource", resource),
            ("Sally-Timestamp", helping.nowIso8601()),
        ])
        path = purl.path or "/"

        keyid = encodeB64(self.hab.kever.serder.verfers[0].raw).decode('utf-8')
        header, unq = httping.siginput(self.hab, "sig0", "POST", path, headers, fields=["Sally-Resource", "@method",
                                                                                        "@path",
                                                                                        "Sally-Timestamp"],
                                       alg="ed25519", keyid=keyid)

        headers.extend(header)
        signage = ending.Signage(markers=dict(sig0=unq), indexed=True, signer=self.hab.pre, ordinal=None, digest=None,
                                 kind=None)

        headers.extend(ending.signature([signage]))

        client.request(
            method='POST',
            path=path,
            qargs=parse.parse_qs(purl.query),
            headers=headers,
            body=raw
        )

        self.clients[said] = (client, clientDoer)

    def validateJourney(self, creder):
        journey_said = self.resolve_type_to_said(JOURNEY_TYPE)
        if creder.schema != journey_said:
            raise kering.ValidationError(f'Invalid schema SAID {creder.schema} for {JOURNEY_TYPE} '
                                         f'credential SAID: {journey_said}')

    def validateJourneyMarkRequest(self, creder):
        request_said = self.resolve_type_to_said(REQUEST_TYPE)
        if creder.schema != request_said:
            raise kering.ValidationError(f'Invalid schema SAID {creder.schema} for {REQUEST_TYPE} '
                                         f'credential SAID: {request_said}')
        self.validateJourneyChain(creder)

    def validateJourneyChain(self, creder):
        edges = creder.chains
        journey_said = edges["journey"]["n"]
        journey_creder = self.reger.creds.get(journey_said)
        if journey_creder is None:
            raise kering.ValidationError(f'{JOURNEY_TYPE} credential not found for {creder.said}')
        self.validateJourney(journey_creder)

    def validateJourneyMark(self, creder):
        request_said = self.resolve_type_to_said(MARK_TYPE)
        if creder.schema != request_said:
            raise kering.ValidationError(f'Invalid schema SAID {creder.schema} for {MARK_TYPE} '
                                         f'credential SAID: {request_said}')
        self.validateRequestChain(creder)

    def validateRequestChain(self, creder):
        edges = creder.chains
        request_said = edges["request"]["n"]
        request_creder = self.reger.creds.get(request_said)
        if request_creder is None:
            raise kering.ValidationError(f'{REQUEST_TYPE} credential not found for {creder.said}')
        self.validateJourneyMarkRequest(request_creder)

    def validateJourneyCharter(self, creder):
        request_said = self.resolve_type_to_said(CHARTER_TYPE)
        if creder.schema != request_said:
            raise kering.ValidationError(f'Invalid schema SAID {creder.schema} for {MARK_TYPE} '
                                         f'credential SAID: {request_said}')
        print('validating journey charter')
        self.validateMarkChain(creder)
        self.validateJourneyChain(creder)

    def validateMarkChain(self, creder):
        edges = creder.chains
        mark_said = edges["mark"]["n"]
        mark_creder = self.reger.creds.get(mark_said)
        if mark_creder is None:
            raise kering.ValidationError(f'{MARK_TYPE} credential not found for {creder.said}')
        # TODO add attribute validation like in validateOfficialRole
        self.validateJourneyMark(mark_creder)

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

    def validateOfficialRoleAuth(self, creder):
        if creder.schema != OOR_AUTH_SCHEMA:
            raise kering.ValidationError(f"invalid schema {creder.schema} for OOR credential {creder.said}")

        edges = creder.chains
        lesaid = edges["le"]["n"]
        le = self.reger.creds.get(lesaid)
        if le is None:
            raise kering.ValidationError(f"LE credential {lesaid} not found for AUTH credential {creder.said}")

        self.validateLegalEntity(le)

    def validateOfficialRole(self, creder):
        if creder.schema != OOR_SCHEMA:
            raise kering.ValidationError(f"invalid schema {creder.schema} for OOR credential {creder.said}")

        edges = creder.chains
        asaid = edges["auth"]["n"]
        auth = self.reger.creds.get(asaid)
        if auth is None:
            raise kering.ValidationError(f"AUTH credential {asaid} not found for OOR credential {creder.said}")

        if auth.crd["a"]["AID"] != creder.subject["i"]:
            raise kering.ValidationError(f"invalid issuee {creder.subject['i']}  doesnt match AUTH value of "
                                         f"{auth.crd['a']['AID']} for OOR " f"credential {creder.said}")

        if auth.crd["a"]["personLegalName"] != creder.subject["personLegalName"]:
            raise kering.ValidationError(f"invalid personLegalNAme {creder.subject['personLegalName']} for OOR "
                                         f"credential {creder.said}")

        if auth.crd["a"]["officialRole"] != creder.subject["officialRole"]:
            raise kering.ValidationError(f"invalid role {creder.subject['officialRole']} for OOR credential"
                                         f" {creder.said}")

        self.validateOfficialRoleAuth(auth)

    def validateQVIChain(self, creder):
        edges = creder.chains
        qsaid = edges["qvi"]["n"]
        qcreder = self.reger.creds.get(qsaid)
        if qcreder is None:
            raise kering.ValidationError(f"QVI credential {qsaid} not found for credential {creder.said}")

        self.validateQualifiedvLEIIssuer(qcreder)

    @staticmethod
    def treasureHuntingJourneyPayload(creder, reger):
        a = creder.crd["a"]
        data = dict(
            schema=creder.schema,
            issuer=creder.issuer,
            issueTimestamp=a["dt"],
            credential=creder.said,
            recipient=a["i"],
            destination=a["destination"],
            treasureSplit=a["treasureSplit"],
            partyThreshold=a["partyThreshold"],
            journeyEndorser=a["journeyEndorser"]
        )

        return data

    @staticmethod
    def journeyMarkRequestPayload(creder, reger):
        a = creder.crd["a"]
        requester_data = a["requester"]
        requester = {
            'firstName': requester_data["firstName"],
            'lastName': requester_data["lastName"],
            'nickname': requester_data["nickname"]
        }
        edges = creder.chains
        journeySaid = edges["journey"]["n"]
        data = dict(
            schema=creder.schema,
            issuer=creder.issuer,
            issueTimestamp=a["dt"],
            credential=creder.said,
            recipient=a["i"],
            requester=requester,
            desiredPartySize=a["desiredPartySize"],
            desiredSplit=a["desiredSplit"],
            journeyCredential=journeySaid
        )

        return data

    @staticmethod
    def journeyMarkPayload(creder, reger):
        a = creder.crd["a"]
        # TODO add in journey credential SAID through reger lookup
        edges = a.chains
        journeySaid = edges["journey"]["n"]

        data = dict(
            schema=creder.schema,
            issuer=creder.issuer,
            issueTimestamp=a["dt"],
            credential=creder.said,
            recipient=a["i"],
            journeyDestination=a["journeyDestination"],
            gatekeeper=a["gatekeeper"],
            negotiatedSplit=a["negotiatedSplit"],
            journeyCredential=journeySaid
        )

        return data

    @staticmethod
    def journeyCharterPayload(creder, reger):
        a = creder.crd["a"]
        edges = creder.chains
        journeySaid = edges["journey"]["n"]
        journey = reger.creds.get(journeySaid)
        jatts = journey.crd["a"]

        markSaid = edges["mark"]["n"]
        mark = reger.creds.get(markSaid)
        requestSaid = mark.chains["request"]["n"]
        request = reger.creds.get(requestSaid)
        ratts = request.crd["a"]

        data = dict(
            schema=creder.schema,
            issuer=creder.issuer,
            issueTimestamp=a["dt"],
            credential=creder.said,
            recipient=a["i"],
            partySize=a["partySize"],
            authorizerName=a["authorizerName"],
            journeyCredential=journeySaid,
            markCredential=markSaid,
            destination=jatts["destination"],
            treasureSplit=jatts["treasureSplit"],
            journeyEndorser=jatts["journeyEndorser"],
            firstName=ratts["requester"]["firstName"],
            lastName=ratts["requester"]["lastName"],
            nickname=ratts["requester"]["nickname"]
        )

        return data

    @staticmethod
    def qviPayload(creder, reger):
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
    def entityPayload(creder, reger):
        a = creder.crd["a"]
        edges = creder.chains
        qsaid = edges["qvi"]["n"]
        data = dict(
            schema=creder.schema,
            issuer=creder.issuer,
            issueTimestamp=a["dt"],
            credential=creder.said,
            recipient=a["i"],
            qviCredential=qsaid,
            LEI=a["LEI"]
        )

        return data

    @staticmethod
    def roleCredentialPayload(creder, reger):
        a = creder.crd["a"]
        edges = creder.chains
        asaid = edges["auth"]["n"]

        auth = reger.creds.get(asaid)
        aedges = auth.chains
        lesaid = aedges["le"]["n"]
        qvi = reger.creds.get(lesaid)
        qedges = qvi.chains
        qsaid = qedges["qvi"]["n"]

        data = dict(
            schema=creder.schema,
            issuer=creder.issuer,
            issueTimestamp=a["dt"],
            credential=creder.said,
            recipient=a["i"],
            authCredential=asaid,
            qviCredential=qsaid,
            legalEntityCredential=lesaid,
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
