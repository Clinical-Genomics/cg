# -*- coding: utf-8 -*-
"""Test FastqHandler"""
from pathlib import Path

from cg.apps.balsamic.fastq import FastqHandler
from coverage.python import os


def test_link_file_count(tmpdir, cg_config, link_family, link_sample, simple_files_data) -> dict:
    """Test method to test that the right number of files are created by linking"""

    # given some fastq-files belonging to family and sample
    link_files = simple_files_data
    assert len(tmpdir.listdir()) == len(link_files)
    link_dir = Path(f'{tmpdir}/{link_family}/fastq')
    assert not os.path.exists(link_dir)

    # when calling the method to link
    FastqHandler(cg_config).link(family=link_family, sample=link_sample,
                                 files=link_files)

    # then the linking should have created on directory for the linked files
    assert os.path.exists(link_dir)
    assert len(tmpdir.listdir()) == len(link_files) + 1

    # then we should have a new directory with one concatenated file per read direction
    assert len([name for name in os.listdir(link_dir)
                if os.path.isfile(os.path.join(link_dir, name))]) == 2


def test_link_file_content(tmpdir, cg_config, link_family, link_sample, simple_files_data,
                           content_r1, content_r2
                           ) -> dict:
    """Test method to test that balsamic files are linked properly"""

    # given some fastq-files belonging to family and sample
    link_files = simple_files_data
    link_dir = Path(f'{tmpdir}/{link_family}/fastq')

    # when calling the method to link
    FastqHandler(cg_config).link(family=link_family, sample=link_sample,
                                 files=link_files)

    # then the first concatenated file should contain 'ABCD' and the other 'DEFG'
    linked_files = [name for name in os.listdir(link_dir) if os.path.isfile(os.path.join(
        link_dir, name))]

    file_contents = []

    for file_name in linked_files:
        file_path = os.path.join(link_dir, file_name)

        with open(file_path, 'rt') as file:
            file_contents.append(file.read())

    assert file_contents[0] == content_r1
    assert file_contents[1] == content_r2
