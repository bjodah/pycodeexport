# -*- coding: utf-8 -*-

import glob
import os
import subprocess

import pytest


tests = glob.glob(os.path.join(os.path.dirname(__file__), '../*_main.py'))


@pytest.mark.parametrize('pypath', tests)
def test_examples(pypath):
    p = subprocess.Popen(
        ['python', pypath, 'clean'],
        cwd=os.path.join(os.path.dirname(__file__), '..'))
    assert p.wait() == 0 # SUCCESS==0
