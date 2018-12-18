import pytest


@pytest.fixture
def valid_fastq_filename_pattern():
    # 'xxx_R_1_.fastq.gz and xxx_R_2_.fastq.gz'
    return r'^.+_R_[1-2]{1}_\.fastq.gz$'
