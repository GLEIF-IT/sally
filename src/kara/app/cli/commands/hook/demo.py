# -*- encoding: utf-8 -*-
"""
kara.cli.commands module

"""
import argparse

import falcon
from hio.base import doing
from hio.core import http
from keri.app import keeping, habbing, directing, configing
from keri.app.cli.common import existing
from keri.end import ending

from kara.core import serving

parser = argparse.ArgumentParser(description='Launch KARA sample web hook server')
parser.set_defaults(handler=lambda args: launch(args),
                    transferable=True)
parser.add_argument('-p', '--http',
                    action='store',
                    default=9923,
                    help="Port on which to listen for web hook event.  Defaults to 9923")


def launch(args, expire=0.0):
    httpPort = args.http

    app = falcon.App(
        middleware=falcon.CORSMiddleware(
            allow_origins='*',
            allow_credentials='*',
            expose_headers=['cesr-attachment', 'cesr-date', 'content-type']))
    app.add_route("/", Listener())

    server = http.Server(port=httpPort, app=app)
    httpServerDoer = http.ServerDoer(server=server)

    print(f"Kara Web Hook Sample listening on {httpPort}")
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
        print("** HEADERS **")
        print(req.headers)
        print("*************")

        print("**** BODY ****")
        body = req.get_media()
        print(body)
        print("**************")


