# -*- encoding: utf-8 -*-
"""
kara.cli.commands module

"""
import argparse

from keri.app import keeping, habbing, directing, configing
from keri.app.cli.common import existing
from keri.end import ending

from kara.core import serving

parser = argparse.ArgumentParser(description='Launch KARA micro-service')
parser.set_defaults(handler=lambda args: launch(args),
                    transferable=True)
parser.add_argument('-p', '--http',
                    action='store',
                    default=9723,
                    help="Port on which to listen for OOBI requests.  Defaults to 9723")
parser.add_argument('-n', '--name',
                    action='store',
                    default="kara",
                    help="Name of controller. Default is kara.")
parser.add_argument('-w', '--web-hook', help='Webhook address for outbound notifications of credential issuance or '
                                             'revocation',
                    action='store',
                    required=True,
                    default=None
                    )
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
parser.add_argument('--listen', '-l', help='run KARA in direct HTTP mode listening for events', action="store_true")


def launch(args, expire=0.0):
    hook = args.web_hook
    name = args.name
    base = args.base
    bran = args.bran
    htp = args.http
    listen = args.listen

    alias = args.alias
    configFile = args.configFile
    configDir = args.configDir

    ks = keeping.Keeper(name=name,
                        base=base,
                        temp=False,
                        reopen=True)

    aeid = ks.gbls.get('aeid')

    cf = None
    if aeid is None:
        if configFile is not None:
            cf = configing.Configer(name=configFile,
                                    base=base,
                                    headDirPath=configDir,
                                    temp=False,
                                    reopen=True,
                                    clear=False)

        hby = habbing.Habery(name=name, base=base, bran=bran, cf=cf)
    else:
        hby = existing.setupHby(name=name, base=base, bran=bran)

    hbyDoer = habbing.HaberyDoer(habery=hby)  # setup doer
    obl = ending.Oobiery(hby=hby)

    doers = [hbyDoer, obl]

    doers += serving.setup(hby, alias, htp, hook, listen)

    print(f"Kara Server listening on {htp}")
    directing.runController(doers=doers, expire=expire)
