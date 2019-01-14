import ntpath
import string
from pathlib import Path
from shutil import copyfile, copy

import pytest


@pytest.fixture
def valid_fastq_filename_pattern():
    """the pattern balsamic file names should match"""
    # 'xxx_R_1_.fastq.gz and xxx_R_2_.fastq.gz'
    return r'^.+_R_[1-2]{1}\.fastq.gz$'


@pytest.fixture
def content():
    """The content the files are made of"""
    return string.ascii_letters


@pytest.fixture
def content_r1(content, simple_files):
    """The content of concatenated r1 """
    return content[0:len(simple_files) // 2]


@pytest.fixture
def content_r2(content, simple_files):
    """The content of concatenated r2 """
    return content[len(simple_files) // 2:len(simple_files)]


@pytest.fixture
def simple(tmpdir, content):
    """Creates a dict with the data to use in the tests"""
    samples = [1]
    flowcells = [1, 2]
    lanes = [1, 2, 3]
    reads = [1, 2]

    simple = {'files': [], 'data': []}
    i = 0

    for sample in samples:
        for read in reads:
            for lane in lanes:
                for flowcell in flowcells:
                    file_path = create_file(tmpdir, sample, flowcell, lane, read, content[i])
                    i += 1

                    simple['files'].append(file_path)
                    data = create_file_data(file_path, flowcell, lane, read)
                    simple['data'].append(data)
    return simple


@pytest.fixture
def simple_files(simple):
    """"Some files to test with"""
    return simple['files']


@pytest.fixture
def simple_files_data(simple):
    """Data for link method"""
    return simple['data']


def create_file(tmpdir, sample, flowcell, lane, read, content):
    """actual file on disk"""

    # create filename
    file_name = f'S{sample}_FC000{flowcell}_L00{lane}_R_{read}.fastq.gz'

    # create path
    file_path = tmpdir / file_name

    # create file content
    file_content = content

    # write content to file
    file_path.write(file_content)

    print(f'created file {file_name} containing: {file_content}')

    return file_path


def create_file_data(file_path, flowcell, lane, read):
    """meta data about a file on disk"""
    data = {
        'path': file_path,
        'lane': lane,
        'flowcell': flowcell,
        'read': read,
        'undetermined': False,
    }
    return data


@pytest.fixture
def cg_config(tmpdir):
    """mock relevant parts of a cg-config"""
    return {'balsamic':
            {'root': tmpdir}}


@pytest.fixture
def link_family():
    """mock family name"""
    return 'family'


@pytest.fixture
def link_sample():
    """mock sample name"""
    return 'sample'

