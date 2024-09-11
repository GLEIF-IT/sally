# -*- encoding: utf-8 -*-
"""
sally.app.commands module

"""
import multicommand

from sally.app.cli import commands


def main():
    parser = multicommand.create_parser(commands)
    args = parser.parse_args()

    try:
        args.handler(args)
    except Exception as ex:
        # print(f"ERR: {ex}")
        # return -1
        raise ex


if __name__ == "__main__":
    main()
