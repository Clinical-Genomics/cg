"""Test FastqHandler"""
import os
from pathlib import Path

from cg.apps.microsalt.fastq import FastqHandler


def test_fastq_link_file_count(tmpdir, cg_config, link_ticket, link_sample, simple_files_data):
    """Test method to test that the right number of files are created by linking"""

    # given some fastq-files belonging to family and sample
    link_files = simple_files_data
    assert len(tmpdir.listdir()) == len(link_files)

    # The fastq files should be linked to /.../fastq/<project>/<sample>/*.fastq.gz.
    link_dir = Path(f"{tmpdir}/fastq/{link_ticket}/{link_sample}")
    assert not os.path.exists(link_dir)

    # when calling the method to link
    FastqHandler(cg_config).link(ticket=link_ticket, sample=link_sample, files=link_files)

    # then the linking should have created on directory for the linked files
    assert os.path.exists(link_dir)
    assert len(tmpdir.listdir()) == len(link_files) + 1
