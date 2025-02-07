import falcon
import sally
from keri.help import nowIso8601


class HealthEnd:
    """
    Basic health check endpoint including a health message, Sally version, and operational metrics
    """

    def __init__(self, cdb = None):
        """
        Adds the CueBaser to allow getting metric counts.
        Defaults to none in case used via demo webhook
        """
        self.cdb = cdb


    def on_get(self, req, resp):
        counts = self.cdb.getCounts() if self.cdb else {}
        resp.status = falcon.HTTP_OK
        resp.media = {
            "message": f"Health is okay. Time is {nowIso8601()}",
            "version": f"{sally.__version__}",
            "counts": counts
        }
