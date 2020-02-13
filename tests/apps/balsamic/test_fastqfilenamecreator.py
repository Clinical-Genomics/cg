"""Test FastqHandlerBalsamic"""
import datetime as dt
import re

from cg.apps.balsamic.fastq import FastqHandler


def test_create(valid_fastq_filename_pattern) -> dict:
    """Test the method that creates balsamic file names for us"""

    # given we have all the necessary inputs to create a filename
    lane = "l"
    flowcell = "fc"
    sample = "s"
    read = "1"
    undetermined = "u"
    optional_date = dt.datetime.now()
    optional_index = "abcdef"
    more = {"undetermined": undetermined, "date": optional_date, "index": optional_index}

    # when calling the method to create a valid filename
    result_filename = FastqHandler.FastqFileNameCreator.create(
        lane=lane, flowcell=flowcell, sample=sample, read=read, more=more
    )

    # then the filename produced is compatible with the filename rules
    assert re.match(valid_fastq_filename_pattern, result_filename)
