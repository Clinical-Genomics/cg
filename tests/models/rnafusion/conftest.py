from typing import List

import pytest


@pytest.fixture(name="rnafusion_sample")
def fixture_rnafusion_sample() -> str:
    """Return sample."""
    return "rnafusion_sample"


@pytest.fixture(name="rnafusion_fastq_forward")
def fixture_rnafusion_fastq_forward() -> List[str]:
    """Return fastq_forward list."""
    return [
        "dir/XXXXXXXX1_000000_S000_L001_R1_001.fastq.gz",
        "dir/XXXXXXXX2_000000_S000_L001_R1_001.fastq.gz",
        "dir/XXXXXXXX3_000000_S000_L001_R1_001.fastq.gz",
        "dir/XXXXXXXX4_000000_S000_L001_R1_001.fastq.gz",
    ]


@pytest.fixture(name="rnafusion_fastq_reverse_same_length")
def fixture_rnafusion_fastq_reverse_same_length() -> List[str]:
    """Return fastq_reverse list, same length as fastq_forward."""
    return [
        "dir/XXXXXXXX1_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX2_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX3_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX4_000000_S000_L001_R2_001.fastq.gz",
    ]


@pytest.fixture(name="rnafusion_fastq_reverse_not_same_length")
def fixture_rnafusion_fastq_reverse_not_same_length() -> List[str]:
    """Return fastq_reverse list, different length as fastq_forward."""
    return [
        "dir/XXXXXXXX1_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX2_000000_S000_L001_R2_001.fastq.gz",
        "dir/XXXXXXXX3_000000_S000_L001_R2_001.fastq.gz",
    ]


@pytest.fixture(name="rnafusion_fastq_reverse_empty")
def fixture_rnafusion_fastq_reverse_empty() -> list:
    """Return empty fastq_reverse list."""
    return []


@pytest.fixture(name="rnafusion_strandedness_acceptable")
def fixture_rnafusion_strandedness_acceptable() -> str:
    """Return an acceptable strandedness."""
    return "reverse"


@pytest.fixture(name="rnafusion_strandedness_not_acceptable")
def fixture_rnafusion_strandedness_not_acceptable() -> str:
    """Return a not acceptable strandedness."""
    return "double_stranded"
