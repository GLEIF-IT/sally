# -*- encoding: utf-8 -*-
"""
sally.cli.commands module

"""
import argparse
import os

from hio.base import doing
from keri.app import keeping, habbing
from keri.app.cli.common import existing

import sally
from sally import ogler, log_name, set_log_level
from sally.app.bootstrapping import BootstrapRunner
from sally.core import serving, scheduling, configing
from sally.core.configing import VerifierConfiger

parser = argparse.ArgumentParser(description='Launch Sally vLEI credential presentation receiver service.')
parser.set_defaults(handler=lambda args: launch(args),
                    transferable=True)

parser.add_argument(
    "-d", "--direct", action="store_true", default=False,
    help="Listen for direct-mode messages on HTTP port.  Default is True")
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
    "-r", "--retry-delay", default=None, type=float, action="store",
    help="failed webhook retry delay in seconds (default 10); independent of processing cadence")
parser.add_argument(
    "-e", "--escrow-timeout", default=None, type=float, action="store",
    help="timeout in seconds for escrowed events not delivered to the web hook (default 600)")
parser.add_argument(
    "-l", "--loglevel", action="store", required=False, default=os.getenv("SALLY_LOG_LEVEL", "INFO"),
    help="Set log level to DEBUG | INFO | WARNING | ERROR | CRITICAL. Default is CRITICAL")


logger = ogler.getLogger(log_name)

def launch(args, expire=0.0):
    """Launch Sally vLEI credential presentation receiver service"""
    # Logging config
    set_log_level(args.loglevel, logger)

    # Parse arguments
    hook = args.web_hook
    name = args.name
    salt = args.salt
    base = args.base
    bran = args.bran
    try:
        http_port = int(args.http)
    except ValueError:
        raise ValueError(f"Invalid port number: {args.http}. Must be an integer.")
    auth = args.auth
    direct = args.direct

    timeout = args.escrow_timeout
    retry = args.retry_delay

    alias = args.alias
    config_file = args.configFile
    config_dir = args.configDir

    # Inception configuration for when Sally bootstraps itself
    incept_file = args.inceptFile
    incept_args = {
        "name": name, "base": base, "alias": alias, "bran": bran,
        "incept_file": incept_file, "config_dir": config_dir
    }

    hby = init_habery(name=name, base=base, bran=bran, config_file=config_file,
                      config_dir=config_dir, salt=salt, retry=retry, timeout=timeout)
    hab = serving.incept_if_new(hby, alias, incept_args)

    # setup doers
    doers = serving.setupDoers(
        hby, hab, alias=alias, http_port=http_port, hook=hook, auth=auth,
        timeout=timeout, retry=retry, direct=direct, incept_args=incept_args,
        tocks=hby.sally_tocks, verifier_config=hby.verifier_config,
    )
    logger.info(f"Sally Server v{sally.__version__} listening on {http_port} with DB version {hby.db.version}")
    logger.info(f"Sally effective tocks (seconds): {hby.sally_tocks}")
    logger.info(f"Sally verifier configuration: {hby.verifier_config}")
    serving.run_doers(doers, expire=expire, tock=hby.sally_tocks["root"])

def init_habery(name, base, bran, config_file, config_dir, salt, *, retry=None, timeout=None):
    """Initialize or reopen the Habery (keystore)"""
    ks = keeping.Keeper(name=name, base=base, temp=False, reopen=True)
    aeid = ks.gbls.get('aeid')

    cf = VerifierConfiger(name=config_file if config_file is not None else name,
                         base=base, headDirPath=config_dir,
                         temp=False, reopen=True, clear=False)
    if aeid is None:
        habery_cfg = dict()
        habery_cfg["salt"] = salt if salt else None # When None causes Habery to randomize salt
        hby = habbing.Habery(name=name, base=base, bran=bran, cf=cf, ks=ks, **habery_cfg)
    else:
        ks.close() # existing.setupHby reopens, so close here to avoid LMDB conflict.
        hby = existing.setupHby(name=name, base=base, bran=bran, cf=cf)

    # Resolve OOBIs for the Habery and the new Hab
    hby.sally_tocks = scheduling.loadTocks(hby.cf)
    hby.verifier_config = configing.loadVerifierConfig(hby.cf, retry=retry, timeout=timeout, default_retry=10.0)
    bootstrap_doist = doing.Doist(limit=hby.verifier_config.bootstrap_timeout_seconds,
                                 tock=hby.sally_tocks["bootstrapRoot"], real=True)
    runner = BootstrapRunner(hby=hby, tymth=bootstrap_doist.tymen(), tocks=hby.sally_tocks)
    bootstrap_doist.do(doers=[runner])
    return hby
