# -*- encoding: utf-8 -*-
"""
sally.cli.commands module

"""
import argparse
import datetime
import json

import falcon
from hio.core import http
from keri.app import directing

parser = argparse.ArgumentParser(description='Launch SALLY sample web hook server')
parser.set_defaults(handler=lambda args: launch(args),
                    transferable=True)
parser.add_argument('-p', '--http',
                    action='store',
                    default=9923,
                    help="Port on which to listen for web hook event.  Defaults to 9923")


def launch(args, expire=0.0):
    httpPort = int(args.http)
    print(f'launching on port {httpPort}')

    app = falcon.App(
        middleware=falcon.CORSMiddleware(
            allow_origins='*',
            allow_credentials='*',
            expose_headers=['cesr-attachment', 'cesr-date', 'content-type']))
    app.add_route("/", Listener())

    server = http.Server(port=httpPort, app=app)
    httpServerDoer = http.ServerDoer(server=server)

    print(f"Sally Web Hook Sample listening on {httpPort}")
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
        print('Gatekeeper | received request')
        body = req.get_media()
        match body['action']:
            case 'iss':
                print(f"Gatekeeper | Valid Credential. Validated at {datetime.datetime.now()}")
                self.debug_request(req, body)
            case 'rev':
                schemaSaid = body['data']['schema']
                credentialSaid = body['data']['credential']
                revocationTimestamp = body['data']['revocationTimestamp']
                print(f"Gatekeeper | Invalid credential {credentialSaid} with schema {schemaSaid}. Revoked on: {revocationTimestamp}")
                self.debug_request(req, body)
            case _:
                print('Unexpected action type')

    def debug_request(self, req, body):
        print("*** HEADERS **")
        print(json.dumps(req.headers, indent=2))
        print("**************")
        print("**** BODY ****")
        print(json.dumps(body, indent=2))
        print("**************")
