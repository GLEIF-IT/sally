# -*- encoding: utf-8 -*-
"""
sally.app.commands module

"""
import os

import multicommand

from sally.app.cli import commands


def main():
    parser = multicommand.create_parser(commands)
    args = parser.parse_args()

    if not hasattr(args, 'handler'):
        parser.print_help()
        return

    try:
        args.handler(args)
    except Exception as ex:
        if os.getenv('DEBUG_KLI'):
            import traceback
            traceback.print_exc()
        else:
            print(f"ERR: {ex}")
        return -1


if __name__ == "__main__":
    main()
