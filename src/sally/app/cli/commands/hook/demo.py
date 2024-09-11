# -*- encoding: utf-8 -*-
"""
sally.cli.commands module

"""
import argparse
import logging

import falcon
from hio.core import http
from keri import help
from keri.app import directing

logger = help.ogler.getLogger()

parser = argparse.ArgumentParser(description='Launch SALLY sample web hook server')
parser.set_defaults(handler=lambda args: launch(args),
                    transferable=True)
parser.add_argument('-p', '--http',
                    action='store',
                    default=9923,
                    help="Port on which to listen for web hook event.  Defaults to 9923")


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
    app.add_route("/", Listener())

    server = http.Server(port=httpPort, app=app)
    httpServerDoer = http.ServerDoer(server=server)

    logger.info(f"Sally Web Hook Sample listening on {httpPort}")
    directing.runController(doers=[httpServerDoer], expire=expire)


class Listener:
    """
    Endpoint for web hook calls that prints events to stdout
    """

    def on_post(self, req, rep):
        """ Responds to web hook event POSTs by printing the results to stdout

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        """
        logger.info("** HEADERS **")
        logger.info(req.headers)
        logger.info("*************")

        logger.info("**** BODY ****")
        body = req.get_media()
        logger.info(body)
        logger.info("**************")
