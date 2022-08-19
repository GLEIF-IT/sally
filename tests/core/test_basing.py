# -*- encoding: utf-8 -*-
"""
tests.db.dbing module

"""
import lmdb
import os

from kara.core import basing


def test_baser():
    """
    Test Baser class
    """
    baser = basing.CueBaser(reopen=True)  # default is to not reopen
    assert isinstance(baser, basing.CueBaser)
    assert baser.name == "cb"
    assert baser.temp is False
    assert isinstance(baser.env, lmdb.Environment)
    assert baser.path.endswith("kara/db/cb")
    assert baser.env.path() == baser.path
    assert os.path.exists(baser.path)
