from typing import Callable

from hio.base import doing
from keri.app import habbing, oobiing

from sally import ogler, log_name
from sally.core import scheduling

logger = ogler.getLogger(log_name)


class BootstrapRunner(doing.DoDoer):
    def __init__(self, hby: habbing.Habery, tymth: Callable, tocks=None):
        """
        Parameters:
            hby (Habery): the hab in which to create the AID, if needed
            tymth (function): the clock time (scheduler tick rate) to use from the parent Doist
            tocks (dict): already resolved coroutine cadences in seconds
        """
        self.tocks = scheduling.loadTocks(hby.cf) if tocks is None else tocks
        self.hby = hby
        self.complete = False
        super(BootstrapRunner, self).__init__(tymth=tymth, tock=self.tocks["bootstrap"])
        self.extend([OobiResolveBootstrapper(hby, self)])

    def recur(self, tyme, deeds=None):
        if self.complete:
            return True
        super(BootstrapRunner, self).recur(tyme, deeds)
        return False

    def configureAndIncept(self):
        """Configure a keystore by resolving OOBIs in config"""
        self.extend(OobiResolveBootstrapper(self.hby, self))

class OobiResolveBootstrapper(doing.Doer):
    """
    Bootstraps OOBI Resolutions for a Habery and an AID, resolving all OOBIs in the bootstrap configuration file.
    """

    def __init__(self, hby: habbing.Habery, parent: BootstrapRunner, tock=0.0, **kwa):
        self.hby = hby
        self.parent = parent
        super(OobiResolveBootstrapper, self).__init__(tock=tock, **kwa)

    def configure_and_incept(self):
        oobi_count = self.hby.db.oobis.cntAll()
        if oobi_count:
            obi = oobiing.Oobiery(hby=self.hby)
            self.parent.extend(obi.doers)

            while oobi_count > self.hby.db.roobi.cntAll():
                yield self.parent.tocks["bootstrapOobi"]

            for (oobi,), obr in self.hby.db.roobi.getItemIter():
                if obr.state in (oobiing.Result.resolved,):
                    logger.info(f"{oobi} succeeded")
                if obr in (oobiing.Result.failed,):
                    logger.error(f"{oobi} failed")

            self.parent.remove(obi.doers)

        wc = [oobi for (oobi,), _ in self.hby.db.woobi.getItemIter()]
        if len(wc) > 0:
            logger.info(f"\nAuthenticating Well-Knowns...")
            authn = oobiing.Authenticator(hby=self.hby)
            self.parent.extend(authn.doers)

            while True:
                cap = []
                for (_,), wk in self.hby.db.wkas.getItemIter(keys=b''):
                    cap.append(wk.url)

                if set(wc) & set(cap) == set(wc):
                    break

                yield self.parent.tocks["bootstrapAuth"]

            self.parent.remove(authn.doers)

        self.parent.complete = True

    def recur(self, tock=0.0, **opts):
        yield from self.configure_and_incept()
        return True
