# -*- coding: utf-8 -*-
"""Test FastqFileConcatenator"""
import filecmp
from cg.apps.balsamic.fastq import FastqFileConcatenator


def test_concatenate(tmpdir, simple_files, content) -> dict:
    """Test method to test that files are concatenated properly"""

    # given we have some files to concatenate and somewhere to store the concatenated file
    assert len(tmpdir.listdir()) == len(simple_files)
    concatenated_filepath = tmpdir + '/concatenated.fastq.gz'

    # when calling the method to concatenate
    FastqFileConcatenator.concatenate(simple_files, concatenated_filepath)

    # then we get a new file that is the concatenation of the others
    assert len(tmpdir.listdir()) == len(simple_files) + 1

    with open(concatenated_filepath, 'rt') as file:
        file_content = file.read()

    assert content[0:len(simple_files)] == file_content
