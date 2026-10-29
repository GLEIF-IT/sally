from hio.base import doing
from hio.help import decking
from keri.core import coring

from sally import ogler, log_name
from sally.core import metrics as metricsmod

logger = ogler.getLogger(log_name)


class TeveryCuery(doing.Doer):
    """
    Processes credential revocation cues and records when a given credential was revoked in the local cue database (CueBaser).
    """

    def __init__(self, cdb, reger, cues=None, metrics=None, **kwa):
        """
        Parameters:
            cdb (CueBaser): instance of CueBaser database
            reger (Reger): Stores ACDC / TEL events
            cues (Deck): collection of events (cue) to process
            metrics (Metrics): shared metrics registry; a private one is used when omitted
        """
        self.cdb = cdb
        self.reger = reger
        self.cues = cues if cues is not None else decking.Deck()
        self.metrics = metrics if metrics is not None else metricsmod.Metrics()

        super(TeveryCuery, self).__init__(**kwa)

    def do(self, tymth, *, tock=0.0, **opts):
        """
        Iterates over the cues Deck and processes each ACDC revocation cue to save the ACDC sender and revocation time in the cue database.

        Inherited Parameters:
            tymth (function): closure for read only injection of cycle time in seconds
            tock (float): cycle time in seconds
        """
        self.wind(tymth)  # Set the clock with cycle time function
        self.tock = tock  # Set the cycle time of this doer
        yield self.tock   # allow priming of this doer to advance to this line

        while True:
            while self.cues:
                cue = self.cues.popleft()
                if cue['kin'] == "revoked":
                    serder = cue["serder"]
                    said = serder.ked["i"]
                    creder = self.reger.creds.get(said)
                    if creder is None:
                        # The ACDC was never presented to this instance so there is nothing
                        # to report to the webhook. Skip it rather than crash the process.
                        logger.error(f"revocation received for unknown credential {said}")
                        continue

                    prefixer = coring.Prefixer(qb64=creder.issuer)
                    saider = coring.Saider(qb64=said)
                    now = coring.Dater()

                    self.cdb.snd.pin(keys=(saider.qb64,), val=prefixer)
                    self.cdb.rev.pin(keys=(saider.qb64,), val=now)
                    self.metrics.inc("sally_revocations_total")

                yield self.tock

            yield self.tock
