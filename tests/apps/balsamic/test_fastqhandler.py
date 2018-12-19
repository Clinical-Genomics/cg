# -*- coding: utf-8 -*-
"""Test FastqHandler"""
from pathlib import Path

from cg.apps.balsamic.fastq import FastqHandler
from coverage.python import os


def test_link(tmpdir, cg_config, link_family, link_sample, link_files) -> dict:
    """Test method to test that balsamic files are linked properly"""

    # given some fastq-files belonging to family and sample
    assert len(tmpdir.listdir()) == len(link_files)
    link_dir = Path(f'{tmpdir}/{link_family}/fastq')
    assert not os.path.exists(link_dir)

    # when calling the method to link
    FastqHandler(cg_config).link(family=link_family, sample=link_sample, files=link_files)

    # then we should have a new directory with one concatenated file per read direction
    assert len(tmpdir.listdir()) == len(link_files) + 1
    print(link_dir)
    assert os.path.exists(link_dir)
    print(os.listdir(link_dir))
    assert len([name for name in os.listdir(link_dir) if os.path.isfile(os.path.join(link_dir, name))]) == 2
