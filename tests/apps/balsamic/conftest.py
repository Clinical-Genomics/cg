"""Fixtures for testing balsamic app"""
import string

import pytest


@pytest.fixture
def valid_fastq_filename_pattern():
    """the pattern balsamic file names should match"""
    # 'xxx_R_1.fastq.gz and xxx_R_2.fastq.gz'
    return r"^.+_R_[1-2]{1}\.fastq.gz$"


def _full_content():
    """The content the files are made of"""
    return string.ascii_letters


@pytest.fixture
def files_content(tmpdir):
    """The content the files are made of"""
    return _full_content()[0 : len(_simple_files(tmpdir))]


@pytest.fixture
def content_r1(tmpdir):
    """The content of concatenated r1 """
    # return full_content[0:len(simple_files) // 2]
    return "".join(simple(tmpdir)["content_r1"])


@pytest.fixture
def content_r2(tmpdir):
    """The content of concatenated r2 """
    # return full_content[len(simple_files) // 2:len(simple_files)]
    return "".join(simple(tmpdir)["content_r2"])


def simple(tmpdir):
    """Creates a dict with the data to use in the tests"""
    flowcells = [1, 2, 3, 4, 5, 6, 7, 8]
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


def _simple_files(tmpdir):
    """"Some files to test with"""
    return simple(tmpdir)["files"]


@pytest.fixture
def simple_files(tmpdir):
    """"Some files to test with"""
    return _simple_files(tmpdir)


@pytest.fixture
def simple_files_data(tmpdir):
    """Data for link method"""
    return simple(tmpdir)["data"]


@pytest.fixture
def simple_files_data_reversed(tmpdir):
    """Data for link method"""
    return simple(tmpdir)["data_reversed"]


def create_file(tmpdir, flowcell, lane, read, file_content):
    """actual file on disk"""

    file_name = f"S1_FC000{flowcell}_L00{lane}_R_{read}.fastq.gz"
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
    return {"balsamic": {"root": tmpdir}}


@pytest.fixture
def link_family():
    """mock case name"""
    return "case"


@pytest.fixture
def link_sample():
    """mock sample name"""
    return "sample"
