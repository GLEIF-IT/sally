from hio.base import doing
from hio.help import decking
from keri import help


logger = help.ogler.getLogger()


class VerificationAgent(doing.DoDoer):
    """
    Doer for running the reporting agent in direct HTTP mode rather than indirect mode.
    Direct mode is used when presenting directly to the reporting agent after resolving the reporting agent OOBI as a Controller OOBI.
    Indirect mode is used when presenting to the reporting agent via a mailbox whether from a witness or a mailbox agent.
    """

    def __init__(self, hab, parser, kvy, tvy, rvy, exc, cues=None, **opts):
        """
        Initializes the ReportingAgent with an identifier (Hab), parser, KEL, TEL, and Exchange message processor
        so that it can process incoming credential presentations.
        """
        self.hab = hab
        self.parser = parser
        self.kvy = kvy
        self.tvy = tvy
        self.rvy = rvy
        self.exc = exc
        self.cues = cues if cues is not None else decking.Deck()
        doers = [doing.doify(self.msgDo), doing.doify(self.escrowDo)]
        super().__init__(doers=doers, **opts)

    def msgDo(self, tymth=None, tock=0.0):
        """
        Processes incoming messages from the parser which triggers the KEL, TEL, Router, and Exchange
        message processor to process credential presentations.
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        if self.parser.ims:
            logger.debug(f"ReportingAgent received:\n%s\n...\n", self.parser.ims[:1024])
        done = yield from self.parser.parsator(local=True)
        return done

    def escrowDo(self, tymth=None, tock=0.0):
        """
        Processes KEL, TEL, Router, and Exchange message processor escrows.
        This ensures that each component processes the messages parsed from the HttpEnd.
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            self.kvy.processEscrows()
            self.rvy.processEscrowReply()
            if self.tvy is not None:
                self.tvy.processEscrows()
            self.exc.processEscrow()

            yield