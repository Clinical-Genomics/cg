from typing import List

import pytest


@pytest.fixture(name="rnafusion_sample")
def fixture_rnafusion_sample() -> str:
    """Return sample."""
    return "rnafusion_sample"


@pytest.fixture(name="rnafusion_fastq_r1")
def fixture_rnafusion_fastq_r1() -> List[str]:
    """Return fastq_r1 list."""
    return [
        "dir/XXXXXXXX1_000000_S000_L001_R1_001.fastq.gz",
        "dir/XXXXXXXX2_000000_S000_L001_R1_001.fastq.gz",
        "dir/XXXXXXXX3_000000_S000_L001_R1_001.fastq.gz",
        "dir/XXXXXXXX4_000000_S000_L001_R1_001.fastq.gz",
    ]


@pytest.fixture(name="rnafusion_fastq_r2_same_length")
def fixture_rnafusion_fastq_r2_same_length() -> List[str]:
    """Return fastq_r2 list, same length as fastq_r1."""
    return [
        "dir/XXXXXXXX1_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX2_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX3_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX4_000000_S000_L001_R2_001.fastq.gz",
    ]


@pytest.fixture(name="rnafusion_fastq_r2_not_same_length")
def fixture_rnafusion_fastq_r2_not_same_length() -> List[str]:
    """Return fastq_r2 list, different length as fastq_r1."""
    return [
        "dir/XXXXXXXX1_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX2_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX3_000000_S000_L001_R2_001.fastq.gz",
    ]


@pytest.fixture(name="rnafusion_fastq_r2_empty")
def fixture_rnafusion_fastq_r2_empty() -> list:
    """Return empty fastq_r2 list."""
    return []


@pytest.fixture(name="rnafusion_strandedness_acceptable")
def fixture_rnafusion_strandedness_acceptable() -> str:
    """Return an acceptable strandedness."""
    return "reverse"


@pytest.fixture(name="rnafusion_strandedness_not_acceptable")
def fixture_rnafusion_strandedness_not_acceptable() -> str:
    """Return a not acceptable strandedness."""
    return "double_stranded"
