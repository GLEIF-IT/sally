# -*- encoding: utf-8 -*-
"""
tests.db.dbing module

"""
import lmdb
import os

from keri.db import subing
from keri.vc import proving
from sally.core import basing


def test_baser():
    """
    Test Baser class
    """
    baser = basing.CueBaser(reopen=True)  # default is to not reopen
    assert isinstance(baser, basing.CueBaser)
    assert baser.name == "cb"
    assert baser.temp is False
    assert isinstance(baser.env, lmdb.Environment)
    assert baser.path.endswith("sally/db/cb")
    assert baser.env.path() == baser.path
    assert os.path.exists(baser.path)

    assert isinstance(baser.snd, subing.CesrSuber)
    assert isinstance(baser.iss, subing.CesrSuber)
    assert isinstance(baser.rev, subing.CesrSuber)
    assert isinstance(baser.recv, subing.SerderSuber)
    assert isinstance(baser.revk, subing.SerderSuber)
    assert isinstance(baser.ack, subing.SerderSuber)

    assert baser.env.stat()['entries'] == 6


