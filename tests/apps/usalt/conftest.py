"""Fixtures for testing balsamic app"""
import string

import pytest


@pytest.fixture
def valid_fastq_filename_pattern():
    """the pattern usalt file names should match"""
    # ACC1234A1_FCAB1ABC2_L1_1.fastq.gz

    # 'sample_flowcell_lane_read.fastq.gz'
    return r"^ACC.+_.+_L[1-8]{1}_[1-2]{1}\.fastq\.gz$"


def _full_content():
    """The content the files are made of"""
    return string.ascii_letters


def simple(tmpdir):
    """Creates a dict with the data to use in the tests"""
    flowcells = [1]
    lanes = [1, 2, 3]
    reads = [1, 2]

    _simple = {
        "files": [],
        "content_r1": [],
        "content_r2": [],
        "data": [],
        "data_reversed": [],
    }
    i = 0

    for read in reads:
        for flowcell in flowcells:
            for lane in lanes:
                content = _full_content()[i]
                file_path = create_file(tmpdir, flowcell, lane, read, content)

                _simple["files"].append(file_path)

                if read == 1:
                    _simple["content_r1"].append(content)
                else:
                    _simple["content_r2"].append(content)

                data = create_file_data(file_path, flowcell, lane, read)
                _simple["data"].append(data)
                _simple["data_reversed"].insert(0, data)
                i += 1

    return _simple


@pytest.fixture
def simple_files_data(tmpdir):
    """Data for link method"""
    return simple(tmpdir)["data"]


def create_file(tmpdir, flowcell, lane, read, file_content):
    """actual file on disk"""

    # ACC1234A1_FCAB1ABC2_L1_1.fastq.gz sample_flowcell_lane_read.fastq.gz
    file_name = f"ACC123_FC000{flowcell}_L{lane}_{read}.fastq.gz"
    file_path = tmpdir / file_name
    file_path.write(file_content)
    return file_path


def create_file_data(file_path, flowcell, lane, read):
    """meta data about a file on disk"""
    data = {
        "path": file_path,
        "lane": lane,
        "flowcell": flowcell,
        "read": read,
        "undetermined": False,
    }
    return data


@pytest.fixture
def cg_config(tmpdir):
    """mock relevant parts of a cg-config"""
    return {"microsalt": {"root": tmpdir}}


@pytest.fixture
def link_ticket():
    """mock ticket number"""
    return "123456"


@pytest.fixture
def link_sample():
    """mock sample name"""
    return "sample"
