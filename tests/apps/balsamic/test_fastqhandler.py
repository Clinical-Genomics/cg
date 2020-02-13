"""Test FastqHandler"""
import os
from pathlib import Path

from cg.apps.balsamic.fastq import FastqHandler


def test_link_file_count(tmpdir, cg_config, link_family, link_sample, simple_files_data):
    """Test method to test that the right number of files are created by linking"""

    # given some fastq-files belonging to family and sample
    link_files = simple_files_data
    assert len(tmpdir.listdir()) == len(link_files)
    link_dir = Path(f"{tmpdir}/{link_family}/fastq")
    assert not os.path.exists(link_dir)

    # when calling the method to link
    FastqHandler(cg_config).link(case=link_family, sample=link_sample, files=link_files)

    # then the linking should have created on directory for the linked files
    assert os.path.exists(link_dir)
    assert len(tmpdir.listdir()) == len(link_files) + 1

    # then we should have a new directory with one concatenated file per read direction
    assert (
        len([name for name in os.listdir(link_dir) if os.path.isfile(os.path.join(link_dir, name))])
        == 2
    )


def test_link_file_content(
    tmpdir, cg_config, link_family, link_sample, simple_files_data, content_r1, content_r2
):
    """Test method to test that balsamic files are linked properly"""

    # given some fastq-files belonging to family and sample
    link_files = simple_files_data
    link_dir = Path(f"{tmpdir}/{link_family}/fastq")

    # when calling the method to link
    FastqHandler(cg_config).link(case=link_family, sample=link_sample, files=link_files)

    # then the first concatenated file should contain 'ABCD' and the other 'DEFG'
    linked_files = [
        name for name in os.listdir(link_dir) if os.path.isfile(os.path.join(link_dir, name))
    ]

    file_contents = []

    for file_name in linked_files:
        file_path = os.path.join(link_dir, file_name)

        with open(file_path, "rt") as file:
            file_contents.append(file.read())

    assert content_r1 in file_contents
    assert content_r2 in file_contents


def test_link_file_content_reversed(
    tmpdir, cg_config, link_family, link_sample, simple_files_data_reversed, content_r1, content_r2
):
    """Test method to test that balsamic files are linked properly"""

    # given some fastq-files belonging to family and sample
    link_files = simple_files_data_reversed
    link_dir = Path(f"{tmpdir}/{link_family}/fastq")

    # when calling the method to link
    FastqHandler(cg_config).link(case=link_family, sample=link_sample, files=link_files)

    # then the first concatenated file should contain 'ABCD' and the other 'DEFG'
    linked_files = [
        name for name in os.listdir(link_dir) if os.path.isfile(os.path.join(link_dir, name))
    ]

    file_contents = []

    for file_name in linked_files:
        file_path = os.path.join(link_dir, file_name)

        with open(file_path, "rt") as file:
            file_contents.append(file.read())

    assert content_r1 in file_contents
    assert content_r2 in file_contents
