from hio.base import doing
from hio.help import decking
from sally import ogler, log_name


logger = ogler.getLogger(log_name)


class VerificationAgent(doing.DoDoer):
    """
    Doer for running the reporting agent in direct HTTP mode rather than indirect mode.
    Direct mode is used when presenting directly to the reporting agent after resolving the reporting agent OOBI as a Controller OOBI.
    Indirect mode is used when presenting to the reporting agent via a mailbox whether from a witness or a mailbox agent.
    """

    def __init__(self, hab, parser, kvy, tvy, rvy, verifier, exc, cues=None, msg_tock=0.0, escrow_tock=0.0, **opts):
        """
        Initializes the ReportingAgent with an identifier (Hab), parser, KEL, TEL, and Exchange message processor
        so that it can process incoming credential presentations.

        Parameters:
            hab (Hab): The identifier (Hab) for the reporting agent.
            parser (Parser): The message parser to handle incoming messages.
            kvy (Kevery): The KEL message processor for handling key events.
            tvy (Tevery): The TEL message processor for handling registry and credential events.
            rvy (Revery): The Reply message processor for handling location, endrole, and other reply of messages.
            verifier (Verifier): The Credential processor for handling credential escrows.
            exc (Exchanger): The Exchanger for managing exchange messages.
            cues (Deck, optional): A data buffer for inter-component communication cues. Defaults to an empty deck
        """
        self.hab = hab
        self.parser = parser
        self.kvy = kvy
        self.tvy = tvy
        self.rvy = rvy
        self.verifier = verifier
        self.exc = exc
        self.cues = cues if cues is not None else decking.Deck()
        doers = [doing.doify(self.msgDo, tock=msg_tock), doing.doify(self.escrowDo, tock=escrow_tock)]
        super().__init__(doers=doers, **opts)

    def msgDo(self, tymth=None, tock=0.0, temp=None, **opts):
        """
        Processes incoming messages from the parser which triggers the KEL, TEL, Router, and Exchange
        message processor to process credential presentations.
        """
        self.wind(tymth)
        _ = (yield tock)

        if self.parser.ims:
            logger.debug(f"ReportingAgent received:\n%s\n...\n", self.parser.ims[:1024])
        for delay in self.parser.parsator(local=True):
            yield tock if delay is None else delay

    def escrowDo(self, tymth=None, tock=0.0, temp=None, **opts):
        """
        Processes KEL, TEL, Router, and Exchange message processor escrows.
        This ensures that each component processes the messages parsed from the HttpEnd.
        """
        self.wind(tymth)
        _ = (yield tock)

        while True:
            self.kvy.processEscrows()
            self.rvy.processEscrowReply()
            if self.tvy is not None:
                self.tvy.processEscrows()
            if self.verifier is not None:
                self.verifier.processEscrows()
            self.exc.processEscrow()

            yield tock
