# -*- encoding: utf-8 -*-
"""
sally.cli.commands module

"""
import argparse
import logging
import pprint

import falcon
from hio.core import http
from keri import help
from keri.app import directing

from sally.core import handling

logger = help.ogler.getLogger()

parser = argparse.ArgumentParser(description='Launch SALLY sample web hook server')
parser.set_defaults(handler=lambda args: launch(args),
                    transferable=True)
parser.add_argument('-p', '--http',
                    action='store',
                    default=9923,
                    help="Port on which to listen for web hook events.  Defaults to 9923")


def launch(args, expire=0.0):
    baseFormatter = logging.Formatter('%(asctime)s [hook] %(levelname)-8s %(message)s')
    baseFormatter.default_msec_format = None
    help.ogler.baseConsoleHandler.setFormatter(baseFormatter)
    help.ogler.level = logging.getLevelName(logging.INFO)
    help.ogler.reopen(name="hook", temp=True, clear=True)

    httpPort = args.http

    app = falcon.App(
        middleware=falcon.CORSMiddleware(
            allow_origins='*',
            allow_credentials='*',
            expose_headers=['cesr-attachment', 'cesr-date', 'content-type']))
    app.add_route("/", WebhookListener())

    server = http.Server(port=httpPort, app=app)
    httpServerDoer = http.ServerDoer(server=server)

    logger.info(f"Sally Web Hook Sample listening on {httpPort}")
    directing.runController(doers=[httpServerDoer], expire=expire)


class WebhookListener:
    """
    Demonstration endpoint for web hook calls that prints events to stdout and stores a simple presentation cache.
    """
    def __init__(self):
        self.received = dict()

    def on_post(self, req, resp):
        """Receives web hook POST events by printing the credential results to stdout and storing presentations them in memory
        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
        """
        logger.info("** HEADERS **")
        logger.info(pprint.pprint(req.headers))
        logger.info("*************")

        logger.info("**** BODY ****")
        body = req.get_media()
        logger.info(pprint.pprint(body))
        logger.info("**************")

        data = body.get("data", {})
        if not data:
            logger.error("No data in body")
            resp.media = {"error": "No data in body"}
            resp.status = falcon.HTTP_400
            return
        type = self._resolve_type(data["schema"])
        if type == "OOR":
            holder = data.get("recipient", "")
            presentation = dict(
                credential=data.get("credential", ""),
                type=type,
                issuer=body.get("actor", ""),
                holder=holder,
                LEI=data.get("LEI", ""),
                personLegalName=data.get("personLegalName", ""),
                officialRole=data.get("officialRole", ""),
            )
            self.received[holder] = presentation
        resp.status = falcon.HTTP_202

    def _resolve_type(self, schema_said):
        """Return human friendly name for schema type"""
        match schema_said:
            case handling.QVI_SCHEMA:
                return "QVI"
            case handling.LE_SCHEMA:
                return "LE"
            case handling.OOR_AUTH_SCHEMA:
                return "OOR Auth"
            case handling.OOR_SCHEMA:
                return "OOR"
            case _:
                raise ValueError(f"Unknown schema type with SAID: {schema_said}")

    def on_get(self, req, resp):
        """
        Tells the presenter if they have presented a credential before.
        Used in testing to determine that a presentation has succeeded.
        """
        holder = req.get_param("holder", required=True)
        if holder in self.received:
            resp.media = self.received[holder]
            resp.status = falcon.HTTP_200
        else:
            resp.media = {"error": f"No credential presented by {holder}"}
            resp.status = falcon.HTTP_404

