"""Test FastqHandlerUsalt"""
import re

from cg.apps.microsalt.fastq import FastqHandler


def test_fastq_create(valid_fastq_filename_pattern) -> dict:
    """Test the method that creates balsamic file names for us"""

    # given we have all the necessary inputs to create a filename
    lane = "1"
    flowcell = "FC"
    sample = "ACC123456"
    read = "1"
    undetermined = "u"

    more = {"undetermined": undetermined}

    # when calling the method to create a valid filename
    result_filename = FastqHandler.FastqFileNameCreator.create(
        lane=lane, flowcell=flowcell, sample=sample, read=read, more=more
    )

    # then the filename produced is compatible with the filename rules
    assert re.match(valid_fastq_filename_pattern, result_filename)
