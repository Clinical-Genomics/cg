# -*- coding: utf-8 -*-
"""Test FastqFileConcatenator"""
import filecmp
from cg.apps.balsamic.fastq import FastqFileConcatenator


def test_concatenate(tmpdir, files_r1, validated_concatenated_r1) -> dict:
    """Test method to test that files are concatenated properly"""

    # given we have some files to concatenate and somewhere to store the concatenated file
    assert len(tmpdir.listdir()) == 2
    concatenated_r1 = tmpdir + '/concatenated.fastq.gz'

    # when calling the method to concatenate
    FastqFileConcatenator.concatenate(files_r1, concatenated_r1)

    # then we get a new file that is the concatenation of the others
    print(tmpdir.listdir())
    assert len(tmpdir.listdir()) == 3
    assert filecmp.cmp(validated_concatenated_r1, concatenated_r1)
