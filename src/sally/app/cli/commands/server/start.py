# -*- encoding: utf-8 -*-
"""
sally.cli.commands module

"""
import argparse
import logging

from keri import help
from keri.app import keeping, habbing, directing, configing, oobiing
from keri.app.cli.common import existing

import sally
from sally.core import serving

help.ogler.level = logging.getLevelName(logging.INFO)
logger = help.ogler.getLogger()

parser = argparse.ArgumentParser(description='Launch SALLY micro-service')
parser.set_defaults(handler=lambda args: launch(args),
                    transferable=True)
parser.add_argument('-p', '--http',
                    action='store',
                    default=9723,
                    help="Port on which to listen for OOBI requests.  Defaults to 9723")
parser.add_argument('-n', '--name',
                    action='store',
                    default="sally",
                    help="Name of controller. Default is sally.")
parser.add_argument('-w', '--web-hook', help='Webhook address for outbound notifications of credential issuance or '
                                             'revocation',
                    action='store',
                    required=True,
                    default=None
                    )
parser.add_argument("--escrow-timeout", "-e", help="timeout (in minutes) for escrowed events that have not been "
                                                   "delivered to the web hook.  Defaults to 10",
                    default=10, type=int,
                    action="store")
parser.add_argument("--retry-delay", "-r", help="retry delay (in seconds) for failed web hook attempts",
                    default=10, type=int,
                    action="store")
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")
parser.add_argument('--alias', '-a', help='human readable alias for the new identifier prefix', required=True)
parser.add_argument('--passcode', help='22 character encryption passcode for keystore (is not saved)',
                    dest="bran", default=None)  # passcode => bran
parser.add_argument("--config-dir", "-c", dest="configDir", help="directory override for configuration data")
parser.add_argument('--config-file',
                    dest="configFile",
                    action='store',
                    default=None,
                    help="configuration filename override")
parser.add_argument('--auth', help='AID or alias of authority for OOBIs and QVI credential issuer', action="store",
                    required=True)
parser.add_argument('--listen', '-l', help='run SALLY in direct HTTP mode listening for events', action="store_true")


def launch(args, expire=0.0):
    base_formatter = logging.Formatter('%(asctime)s [sally] %(levelname)-8s %(message)s')
    base_formatter.default_msec_format = None
    help.ogler.baseConsoleHandler.setFormatter(base_formatter)
    help.ogler.level = logging.getLevelName(logging.INFO)
    help.ogler.reopen(name="sally", temp=True, clear=True)

    hook = args.web_hook
    name = args.name
    base = args.base
    bran = args.bran
    http_port = args.http
    auth = args.auth

    listen = args.listen
    timeout = args.escrow_timeout
    retry = args.retry_delay

    alias = args.alias
    config_file = args.configFile
    config_dir = args.configDir

    ks = keeping.Keeper(name=name,
                        base=base,
                        temp=False,
                        reopen=True)

    aeid = ks.gbls.get('aeid')

    cf = None
    if aeid is None:
        if config_file is not None:
            cf = configing.Configer(name=config_file,
                                    base=base,
                                    headDirPath=config_dir,
                                    temp=False,
                                    reopen=True,
                                    clear=False)

        hby = habbing.Habery(name=name, base=base, bran=bran, cf=cf)
    else:
        hby = existing.setupHby(name=name, base=base, bran=bran)

    hbyDoer = habbing.HaberyDoer(habery=hby)  # setup doer
    obl = oobiing.Oobiery(hby=hby)

    doers = [hbyDoer, *obl.doers]

    doers += serving.setup(hby, alias=alias, httpPort=http_port, hook=hook, auth=auth,
                           listen=listen, timeout=timeout, retry=retry)

    logger.info(f"Sally server version {sally.__version__} and database version {hby.db.version}")
    logger.info(f"Sally Server listening on {http_port}")
    directing.runController(doers=doers, expire=expire)