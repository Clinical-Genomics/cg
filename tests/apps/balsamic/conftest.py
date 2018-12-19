import ntpath
from pathlib import Path
from shutil import copyfile, copy

import pytest


@pytest.fixture
def valid_fastq_filename_pattern():
    # 'xxx_R_1_.fastq.gz and xxx_R_2_.fastq.gz'
    return r'^.+_R_[1-2]{1}\.fastq.gz$'


@pytest.fixture
def files_r1(tmpdir):
    fixture_file1 = 'tests/fixtures/DEMUX/160219_D00410_0217_AHJKMYBCXX/Unaligned5/Project_337334' \
                    '/Sample_ADM1136A3_XTC08/ADM1136A3_XTC08_AGTGGTCA_L001_R1_001.fastq.gz'
    fixture_file2 = 'tests/fixtures/DEMUX/160219_D00410_0217_AHJKMYBCXX/Unaligned5/Project_337334' \
                    '/Sample_ADM1136A3_XTC08/ADM1136A3_XTC08_AGTGGTCA_L002_R1_001.fastq.gz'
    testdir_file1 = Path(tmpdir, ntpath.basename(fixture_file1))
    testdir_file2 = Path(tmpdir, ntpath.basename(fixture_file2))
    copy(fixture_file1, tmpdir)
    copy(fixture_file2, tmpdir)
    return [testdir_file1, testdir_file2]


@pytest.fixture
def files_r2(tmpdir):
    fixture_file1 = 'tests/fixtures/DEMUX/160219_D00410_0217_AHJKMYBCXX/Unaligned5/Project_337334' \
                    '/Sample_ADM1136A3_XTC08/ADM1136A3_XTC08_AGTGGTCA_L001_R2_001.fastq.gz'
    fixture_file2 = 'tests/fixtures/DEMUX/160219_D00410_0217_AHJKMYBCXX/Unaligned5/Project_337334' \
                    '/Sample_ADM1136A3_XTC08/ADM1136A3_XTC08_AGTGGTCA_L002_R2_001.fastq.gz'
    testdir_file1 = Path(tmpdir, ntpath.basename(fixture_file1))
    testdir_file2 = Path(tmpdir, ntpath.basename(fixture_file2))
    copy(fixture_file1, tmpdir)
    copy(fixture_file2, tmpdir)
    return [testdir_file1, testdir_file2]


@pytest.fixture
def validated_concatenated_r1(tmpdir):
    return 'tests/fixtures/apps/balsamic/ADM1136A3_XTC08_AGTGGTCA_concat_R1_001.fastq.gz'


@pytest.fixture
def validated_concatenated_r2(tmpdir):
    return 'tests/fixtures/apps/balsamic/ADM1136A3_XTC08_AGTGGTCA_concat_R2_001.fastq.gz'


@pytest.fixture
def cg_config(tmpdir):
    return {'balsamic':
            {'root': tmpdir}}


@pytest.fixture
def link_family():
    return 'family'


@pytest.fixture
def link_sample():
    return 'sample'


@pytest.fixture
def link_files(tmpdir, files_r1, files_r2):
    file_data = []

    lane = 1
    for file in files_r1:
        data = {
            'path': file,
            'lane': int(lane),
            'flowcell': 'AHJKMYBCXX',
            'read': int(1),
            'undetermined': False,
        }
        lane = 2
        file_data.append(data)

    for file in files_r2:
        data = {
            'path': file,
            'lane': int(lane),
            'flowcell': 'AHJKMYBCXX',
            'read': int(2),
            'undetermined': False,
        }
        lane = 2
        file_data.append(data)

    return file_data






















