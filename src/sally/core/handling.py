# -*- encoding: utf-8 -*-
"""
SALLY
sally.core.handling module

EXN Message handling
"""
import datetime
import json
from base64 import urlsafe_b64encode as encodeB64
from typing import List
from urllib import parse

from hio.base import doing, Doer
from hio.core import http
from hio.help import Hict
from keri import help, kering
from keri.core import coring
from keri.peer import exchanging
from keri.end import ending
from keri.help import helping
from sally.core import httping

logger = help.ogler.getLogger()

# vLEI ACDC schema SAIDs
QVI_SCHEMA = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
LE_SCHEMA = "ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY"
OOR_AUTH_SCHEMA = "EKA57bKBKxr_kN7iN5i7lMUxpMG-s19dRcmov1iDxz-E"
OOR_SCHEMA = "EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy"

# makes log messages nicer
type_to_name = {
    QVI_SCHEMA: "QVI",
    LE_SCHEMA: "LE",
    OOR_AUTH_SCHEMA: "OOR Auth",
    OOR_SCHEMA: "OOR"
}


def loadHandlers(cdb, hby, notifier, parser) -> List[Doer]:
    """
    Returns an array of Doers that are handlers for the peer-to-peer exchange messages.
    Sally only uses the notification handler for ACDC presentations.

    Parameters:
        cdb (CueBaser): communication escrow database environment
        hby (Habery): identifier database environment (master keystore)
        notifier (Notifier): Notifications
        parser (Parser): to parse and process each message referred to in an EXN message
    """
    return [PresentationProofHandler(cdb=cdb, hby=hby, notifier=notifier, parser=parser)]


class PresentationProofHandler(doing.Doer):
    """
    Processor for responding to peer-to-peer (exn) notification messages of IPEX Grant presentation proofs.

    """

    def __init__(self, cdb, hby, notifier, parser, **kwa):
        """ Initialize instance

        Parameters:
            cdb (CueBaser): communication escrow database environment
            notifier(Notifier): to read notifications to processes exns
            **kwa (dict): keyword arguments passes to super Doer

        """
        self.cdb = cdb
        self.hby = hby
        self.notifier = notifier
        self.parser = parser
        super(PresentationProofHandler, self).__init__()

    def processNotes(self):
        """
        Handles incoming IPEX Grant presentations by processing the notification queue that is populated when IPEX Grant events occur, which is what happens when a cred

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.

        The payload of the notification exn message is expected to have the following format:
        {
            "r": "/exn/ipex/grant",
            "d": "SAID of the credential"
        }
        The IPEX Grant EXN is then loaded from the Exchanger database.
        The EXN is expected to have the following format:
        {
            "e": { // embedded data in an exchange message.
                "anc": // SerderKERI: anchoring interaction event of the issuance event. Has a reference to the issuance
                {
                    "v":"KERI10JSON00013a_",                                     // CESR version string of this event
                    "t":"ixn",                                                   // KEL Event type
                    "d":"EGhSHKIV5-nkeirdkqzqsvmeF1FXw_yH8NvPSAY1Rgyd",          // SAID digest of the anchoring interaction event
                    "i":"EMl4RhuR_JxpiMd1N8DEJEhTxM3Ovvn9Xya8AN-tiUbl",          // Identifier of the issuer
                    "s":"2",                                                     // Sequence number in the issuer's KEL of the anchoring interaction event.
                    "p":"ED1kkh5_ECYriK-j2gSv6Zjr5way88XVhwRCxk5zoTRG",          // The previous event's digest
                    "a":[ // The anchoring interaction event's seal. Anchors both the issuance TEL event below and the associated ACDC below to the issuer's KEL.
                        {
                            "i":"EElymNmgs1u0mSaoCeOtSsNOROLuqOz103V3-4E-ClXH",  // SAID digest of the ACDC
                            "s": "0",                                            // Sequence number of the TEL event for the TEL associated with the ACDC anchored in this event.
                            "d":"ECUw7AdWEE3fvr7dgbFDXj0CEZuJTTa_H8-iLLAmIUPO"   // SAID digest of the TEL event for the TEL associated with the ACDC anchored in this event.
                        }
                    ]
                },
                "iss": // SerderKERI: registry issuance TEL event body. Has a reference to the ACDC credential.
                {
                    "v":"KERI10JSON0000ed_",                             // CESR version string of this event
                    "t":"iss",                                           // TEL Event type
                    "d":"ECUw7AdWEE3fvr7dgbFDXj0CEZuJTTa_H8-iLLAmIUPO",  // SAID digest of the issuance TEL event.
                    "i":"EElymNmgs1u0mSaoCeOtSsNOROLuqOz103V3-4E-ClXH",  // SAID digest of the ACDC. This refers to the ACDC below.
                    "s":"0",                                             // Sequence number of the TEL issuance event
                    "ri":"EB-u4VAF7A7_GR8PXJoAVHv5X9vjtXew8Yo6Z3w9mQUQ", // Registry identifier of the issuer
                    "dt":"2021-06-27T21:26:21.233257+00:00"              // The datetime the issuance event was created
                },
                "acdc":  // SerderACDC: credential body. The iss event has a reference to this event
                {
                    "v":"ACDC10JSON000197_",                              // CESR version string of this ACDC. indicates serialization type and protocol type
                    "d":"EElymNmgs1u0mSaoCeOtSsNOROLuqOz103V3-4E-ClXH",   // SAID digest of the ACDC
                    "i":"EMl4RhuR_JxpiMd1N8DEJEhTxM3Ovvn9Xya8AN-tiUbl",   // Issuer identifier of the credential
                    "ri":"EB-u4VAF7A7_GR8PXJoAVHv5X9vjtXew8Yo6Z3w9mQUQ",  // Registry identifier that issued this credential
                    "s":"EMQWEcCnVRk1hatTNyK3sIykYSrrFvafX3bHQ9Gkk1kC",   // Schema identifier of the credential
                    "a": { // The credential's attributes; the data the credential contains
                        "d":"EO9_6NattzsFiO8Fw1cxjYmDjOsKKSbootn-wXn9S3iB",  // SAID digest of the attributes section
                        "dt":"2021-06-27T21:26:21.233257+00:00",             // The datetime the credential was created
                        "i":"EMl4RhuR_JxpiMd1N8DEJEhTxM3Ovvn9Xya8AN-tiUbl",  // The identifier of the credential's subject (issuee)
                        "LEI":"254900OPPU84GM83MG36"                         // The Legal Entity Identifier of the credential's subject. This is the data for this credential, a QVI-like credential.
                    }
                }
            }
        }
        """
        for keys, notice in self.notifier.noter.notes.getItemIter():
            logger.info(f"Processing notice {notice.pretty()}")
            attrs = notice.attrs
            route = attrs['r']

            if route == '/exn/ipex/grant':
                # said of grant message
                said = attrs['d']
                exn, pathed = exchanging.cloneMessage(self.hby, said=said)
                embeds = exn.ked['e']

                for label in ("anc", "iss", "acdc"):
                    ked = embeds[label]
                    sadder = coring.Sadder(ked=ked)
                    ims = bytearray(sadder.raw) + pathed[label]
                    self.parser.parseOne(ims=ims)

                acdc = embeds["acdc"]
                said = acdc['d']

                sender = acdc['i']
                prefixer = coring.Prefixer(qb64=sender)

                self.cdb.snd.pin(keys=(said,), val=prefixer)
                self.cdb.iss.pin(keys=(said,), val=coring.Dater())

            # deleting wether its a grant or not, since we only process grant
            self.notifier.noter.notes.rem(keys=keys)

        return False

    def recur(self, tyme):
        """
        On each iteration process exchange (exn) notifications of IPEX Grant presentation notifications.
        """
        self.processNotes()
        return False  # Loop infinitely - long-running Doer task


class Communicator(doing.DoDoer):
    """
    Communicator is responsible for communicating to the webhook the receipt and successful
    verification of credential presentation and revocation messages from external third parties via
    an HTTP API call to the configured webhook URL.
    """

    def __init__(self, hby, hab, cdb, reger, auth, hook, timeout=10, retry=3.0):
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

        super(Communicator, self).__init__(doers=[doing.doify(self.escrowDo)])

    def processPresentations(self):
        """
        Validate presentations move them to the "received" key/value area if its credential chain
        validates and the credential is not revoked. Otherwise, remove the presentation from the escrow.
        """

        for (said,), dater in self.cdb.iss.getItemIter():
            # cancel presentations that have been around longer than timeout
            now = helping.nowUTC()
            logger.info(f"looking for credential {said}")
            if now - dater.datetime > datetime.timedelta(minutes=self.timeout):
                self.cdb.iss.rem(keys=(said,))
                continue

            if self.reger.saved.get(keys=(said,)) is not None:
                creder = self.reger.creds.get(keys=(said,))
                try:
                    regk = creder.regi
                    state = self.reger.tevers[regk].vcState(creder.said)
                    if state is None or state.et not in (kering.Ilks.iss, kering.Ilks.bis):
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
        """
        Ensure revocation CESR data is fully received before moving it to the "revoked to be processed" key/value area.
        """

        for (said,), dater in self.cdb.rev.getItemIter():

            # cancel revocations that have been around longer than timeout
            now = helping.nowUTC()
            if now - dater.datetime > datetime.timedelta(minutes=self.timeout):
                self.cdb.rev.rem(keys=(said,))
                continue

            creder = self.reger.creds.get(keys=(said,))
            if creder is None:  # received revocation before credential.  probably an error but let it timeout
                continue

            regk = creder.regi
            state = self.reger.tevers[regk].vcState(creder.said)
            if state is None:  # received revocation before status.  probably an error but let it timeout
                continue

            elif state.et in (kering.Ilks.iss, kering.Ilks.bis):  # haven't received revocation event yet
                continue

            elif state.et in (kering.Ilks.rev, kering.Ilks.brv):  # revoked
                self.cdb.rev.rem(keys=(said,))
                self.cdb.revk.pin(keys=(said, dater.qb64), val=creder)

    def processReceived(self, db, action):
        """
        Prepare the appropriate payload for issuances or revocations based on schema type and send
        the payload in a request to the webhook URL.
        """

        for (said, dates), creder in db.getItemIter():
            if said not in self.clients:
                resource = creder.schema
                actor = creder.issuer
                if action == "iss":  # presentation of issued credential
                    if creder.schema == QVI_SCHEMA:
                        data = self.qviPayload(creder)
                    elif creder.schema == LE_SCHEMA:
                        data = self.entityPayload(creder)
                    elif creder.schema == OOR_SCHEMA:
                        data = self.roleCredentialPayload(self.reger, creder)
                    else:
                        logger.error(f"invalid credential with schema {creder.schema} said {creder.said} issuer {creder.issuer}")
                        raise kering.ValidationError("this will never happen because all credentials that get here are"
                                                     " valid")
                else:  # revocation of credential
                    data = self.revokePayload(creder)

                logger.info(f"Sending {action} of {type_to_name[creder.schema]} to {self.hook} with SAID {said}")
                logger.info(f"Payload: \n{json.dumps(data, indent=1)}\n")

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
        """Once a webhook request is acknowledged then remove it from the ack queue."""
        for (said,), creder in self.cdb.ack.getItemIter():
            # TODO: generate EXN ack message with credential information
            logger.info(f"ACK for credential {said} will be sent to {creder.issuer}")
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
                logger.error(e)

            yield self.retry

    def processEscrows(self):
        """
        Process communication pipelines for presentations, revocations, and webhook HTTP request acknowledgements.

        """
        self.processPresentations()
        self.processRevocations()
        self.processReceived(db=self.cdb.recv, action="iss")
        self.processReceived(db=self.cdb.revk, action="rev")
        self.processAcks()

    def request(self, said, resource, action, actor, data):
        """
        Generate and launch HTTP request to remote webhook URL.
        Adds custom Sally-Resource and Sally-Timestamp headers.

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
        header, unq = httping.siginput(
            self.hab, "sig0", "POST", path, headers,
            fields=[
                "Sally-Resource",
                "@method",
                "@path",
                "Sally-Timestamp"
            ],
            alg="ed25519",
            keyid=keyid
        )

        headers.extend(header)
        signage = ending.Signage(
            markers=dict(sig0=unq), indexed=True, signer=self.hab.pre, ordinal=None, digest=None, kind=None)

        headers.extend(ending.signature([signage]))

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
            logger.info("Creder has an issue: %s", creder.said)
            logger.debug("Creder Body:\n%s\n", creder.pretty())
            raise kering.ValidationError(f"QVI credential not issued by known valid issuer. Expected {self.auth} found {creder.issuer}")

    def validateLegalEntity(self, creder):
        """Validate schema of LE credential and QVI chain"""
        if creder.schema != LE_SCHEMA:
            raise kering.ValidationError(f"invalid schema {creder.schema} for LE credential {creder.said}")

        self.validateQVIChain(creder)

    def validateOfficialRoleAuth(self, creder):
        """Validate schema of OOR Auth credential and the LE chain"""
        if creder.schema != OOR_AUTH_SCHEMA:
            raise kering.ValidationError(f"invalid schema {creder.schema} for OOR credential {creder.said}")

        if creder is None or creder.edge is None:
            raise kering.ValidationError(f"OOR Auth credential does not have expected 'le' edge")
        edges = creder.edge
        lesaid = edges["le"]["n"]
        le = self.reger.creds.get(lesaid)
        if le is None:
            raise kering.ValidationError(f"LE credential {lesaid} not found for AUTH credential {creder.said}")

        self.validateLegalEntity(le)

    def validateOfficialRole(self, creder):
        """Validate OOR schema, the OOR Auth chain, and that the data attributes from the OOR Auth match the OOR credential data"""
        if creder.schema != OOR_SCHEMA:
            raise kering.ValidationError(f"invalid schema {creder.schema} for OOR credential {creder.said}")

        if creder is None or creder.edge is None:
            raise kering.ValidationError(f"OOR credential does not have expected 'auth' edge")
        edges = creder.edge
        asaid = edges["auth"]["n"]
        auth = self.reger.creds.get(asaid)
        if auth is None:
            logger.error(f"AUTH credential {asaid} not found for OOR credential {creder.said}")
            raise kering.ValidationError(f"AUTH credential {asaid} not found for OOR credential {creder.said}")

        if auth.sad["a"]["AID"] != creder.attrib["i"]:
            raise kering.ValidationError(f"invalid issuee {creder.attrib['i']}  doesnt match AUTH value of "
                                         f"{auth.sad['a']['AID']} for OOR " f"credential {creder.said}")

        if auth.sad["a"]["personLegalName"] != creder.attrib["personLegalName"]:
            raise kering.ValidationError(f"invalid personLegalNAme {creder.attrib['personLegalName']} for OOR "
                                         f"credential {creder.said}")

        if auth.sad["a"]["officialRole"] != creder.attrib["officialRole"]:
            raise kering.ValidationError(f"invalid role {creder.attrib['officialRole']} for OOR credential"
                                         f" {creder.said}")

        self.validateOfficialRoleAuth(auth)

    def validateQVIChain(self, creder):
        """Validate that the LE credential has the QVI edge and the QVI chain is valid"""
        if creder is None or creder.edge is None:
            raise kering.ValidationError(f"LE credential does not have expected 'qvi' edge")
        edges = creder.edge
        qsaid = edges["qvi"]["n"]
        qcreder = self.reger.creds.get(qsaid)
        if qcreder is None:
            raise kering.ValidationError(f"QVI credential {qsaid} not found for credential {creder.said}")

        try:
            self.validateQualifiedvLEIIssuer(qcreder)
        except kering.ValidationError as ex:
            logger.info("QVI credential %s failed QVI validation: %s", qsaid, ex)
            logger.debug("QVI credential body:\n%s\n", qcreder.pretty())
            raise ex

    @staticmethod
    def qviPayload(creder):
        """Creates a QVI credential payload to send to the webhook"""
        a = creder.sad["a"]
        data = dict(
            type=type_to_name[creder.schema],
            schema=creder.schema,
            issuer=creder.issuer,
            issueTimestamp=a["dt"],
            credential=creder.said,
            recipient=a["i"],
            LEI=a["LEI"]
        )

        return data

    @staticmethod
    def entityPayload(creder):
        """Creates a legal entity payload to send to the webhook"""
        a = creder.sad["a"]
        if creder is None or creder.edge is None:
            raise kering.ValidationError(f"LE credential does not have expected 'qvi' edge")
        edges = creder.edge
        qsaid = edges["qvi"]["n"]
        data = dict(
            type=type_to_name[creder.schema],
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
    def roleCredentialPayload(reger, creder):
        """Creates an OOR credential payload to send to the webhook"""
        a = creder.sad["a"]
        if creder is None or creder.edge is None:
            raise kering.ValidationError(f"OOR credential does not have expected 'auth' edge")
        edges = creder.edge
        asaid = edges["auth"]["n"]

        auth = reger.creds.get(asaid)
        if auth is None or auth.edge is None:
            raise kering.ValidationError(f"OOR credential does not have expected 'le' edge")
        aedges = auth.edge
        lesaid = aedges["le"]["n"]
        qvi = reger.creds.get(lesaid)
        if qvi is None or qvi.edge is None:
            raise kering.ValidationError(f"OOR credential does not have expected 'qvi' edge")
        qedges = qvi.edge
        qsaid = qedges["qvi"]["n"]

        data = dict(
            type=type_to_name[creder.schema],
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
        """Creates a revocation payload to send to the webhook"""
        regk = creder.regi
        state = self.reger.tevers[regk].vcState(creder.said)

        data = dict(
            type=type_to_name[creder.schema],
            schema=creder.schema,
            credential=creder.said,
            revocationTimestamp=state.dt
        )

        return data
