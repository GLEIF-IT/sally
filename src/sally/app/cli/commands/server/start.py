# -*- encoding: utf-8 -*-
"""
sally.cli.commands module

"""
import argparse
import logging
import os

from keri import help
from keri.app import keeping, habbing, directing, configing, oobiing
from keri.app.cli.commands import incept
from keri.app.cli.common import existing

import sally
from sally.core import serving

parser = argparse.ArgumentParser(description='Launch Sally vLEI credential presentation receiver service.')
parser.set_defaults(handler=lambda args: launch(args),
                    transferable=True)

parser.add_argument(
    '-p', '--http', action='store', default=9723,
    help="Port on which to listen for OOBI requests.  Defaults to 9723")
parser.add_argument(
    '-n', '--name', action='store', default="sally",
    help="Name of controller. Default is sally.")
parser.add_argument(
    '-b', '--base', required=False, default="",
    help='additional optional prefix to file location of KERI keystore')
parser.add_argument(
    "-c", "--config-dir", dest="configDir",
    help="directory override for configuration data")
parser.add_argument(
    "-f", '--config-file', dest="configFile", action='store', default=None,
    help="Habery (keystore) configuration filename")
parser.add_argument(
    "-i", "--incept-file", dest="inceptFile", action='store', default=None,
    help="inception configuration filename")
parser.add_argument(
    '-a', '--alias', required=True,
    help='human readable alias for the new identifier prefix')
parser.add_argument(
    '-s', '--salt', required=False,
    help='qualified base64 salt for creating key pairs')
parser.add_argument(
    '--passcode', dest="bran", default=None,
    help='21 character encryption passcode for keystore (is not saved)')
parser.add_argument(
    '-w', '--web-hook', action='store', required=True, default=None,
    help='Webhook address for outbound notifications of credential issuance or revocation')
parser.add_argument(
    '--auth', action="store", required=True,
    help='AID or alias of authority for OOBIs and QVI credential issuer')
parser.add_argument(
    "-r", "--retry-delay", default=10, type=int, action="store",
    help="retry delay (in seconds) for failed web hook attempts")
parser.add_argument(
    "-e", "--escrow-timeout", default=10, type=int, action="store",
    help="timeout (in minutes) for escrowed events that have not been delivered to the web hook.  Defaults to 10")
parser.add_argument(
    "-l", "--loglevel", action="store", required=False, default=os.getenv("SALLY_LOG_LEVEL", "INFO"),
    help="Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL")

help.ogler.level = logging.getLevelName(logging.INFO)
logger = help.ogler.getLogger()

def launch(args, expire=0.0):
    """Launch Sally vLEI credential presentation receiver service"""
    base_formatter = logging.Formatter('%(asctime)s [sally] %(levelname)-8s %(message)s')
    base_formatter.default_msec_format = None
    help.ogler.baseConsoleHandler.setFormatter(base_formatter)
    help.ogler.level = logging.getLevelName(args.loglevel.upper())
    logger.setLevel(help.ogler.level)
    help.ogler.reopen(name="sally", temp=True, clear=True)

    hook = args.web_hook
    name = args.name
    salt = args.salt
    base = args.base
    bran = args.bran
    incept_file = args.inceptFile
    http_port = args.http
    auth = args.auth

    timeout = args.escrow_timeout
    retry = args.retry_delay

    alias = args.alias
    config_file = args.configFile
    config_dir = args.configDir

    ks = keeping.Keeper(name=name, base=base, temp=False, reopen=True)
    aeid = ks.gbls.get('aeid')

    cf = None
    if aeid is None:
        if config_file is not None:
            cf = configing.Configer(name=config_file, base=base, headDirPath=config_dir,
                                    temp=False, reopen=True, clear=False)
        habery_cfg = dict()
        habery_cfg["salt"] = salt
        hby = habbing.Habery(name=name, base=base, bran=bran, cf=cf, **habery_cfg)
    else:
        hby = existing.setupHby(name=name, base=base, bran=bran)

    hbyDoer = habbing.HaberyDoer(habery=hby)  # setup doer
    obl = oobiing.Oobiery(hby=hby)

    doers = [hbyDoer, *obl.doers]
    doers += serving.setup(
        hby, alias=alias, httpPort=http_port, hook=hook, auth=auth, timeout=timeout, retry=retry,
        incept_args=inception_args(
            name=name, base=base, alias=alias, bran=bran, inceptFile=incept_file, config_dir=config_dir))

    logger.info(f"Sally Server v{sally.__version__} listening on {http_port} with DB version {hby.db.version}")
    directing.runController(doers=doers, expire=expire)


def inception_args(name=None, base=None, alias=None, bran=None, inceptFile=None, config_dir=None):
    """
    Inception configuration for Sally's identifier prefix

    This uses an object so that it can be merged with the incept file configuration like the
    multicommand args object by using object properties rather than dictionary keys, which is what
    incept.mergeArgsWithFile expects.
    """
    class Object(object):
        pass
    icp_args = Object()
    icp_args.name = name
    icp_args.base = base
    icp_args.alias = alias
    icp_args.bran = bran
    icp_args.file = inceptFile if config_dir is None else os.path.join(config_dir, inceptFile)
    icp_args.transferable = None
    icp_args.icount = None
    icp_args.wits = []
    icp_args.toad = None
    icp_args.isith = None
    icp_args.ncount = None
    icp_args.nsith = None
    icp_args.delpre = None
    icp_args.est_only = None
    icp_args.data = None
    return incept.mergeArgsWithFile(icp_args).__dict__