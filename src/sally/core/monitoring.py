import falcon
import sally
from keri.help import nowIso8601


class HealthEnd:
    """
    Basic health check endpoint including a health message, Sally version, and operational metrics
    """

    def __init__(self, cdb):
        """Adds the CueBaser to allow getting metric counts"""
        self.cdb = cdb


    def on_get(self, req, resp):
        counts = self.cdb.getCounts()
        resp.status = falcon.HTTP_OK
        resp.media = {
            "message": f"Health is okay. Time is {nowIso8601()}",
            "version": f"{sally.__version__}",
            "counts": counts
        }