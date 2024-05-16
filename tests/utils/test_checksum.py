from pathlib import Path

import pytest

from cg.constants import FileExtensions
from cg.utils.checksum.checksum import check_md5sum, extract_md5sum, is_md5sum_correct


def test_checksum(fastq_file: Path):
    """Tests if the function correctly calculates md5sum and returns the correct result."""
    # GIVEN a fastq file with a correct md5 file and a fastq file with an incorrect md5 file
    bad_md5sum_file_path: Path = fastq_file.parent.joinpath("fastq_run_R1_001.fastq.gz")

    # THEN a file with a correct md5 sum should return true
    assert check_md5sum(file_path=fastq_file, md5sum="a95cbb265540a2261fce941059784fd1")

    # THEN a file with an incorrect md5 sum should return false
    assert not check_md5sum(
        file_path=bad_md5sum_file_path, md5sum="c690b0124173772ec4cbbc43709d84ee"
    )


def test_extract_checksum(fastq_file: Path):
    """Tests if the function successfully extract the correct md5sum."""

    # GIVEN a file containing a md5sum
    md5sum_file = Path(f"{fastq_file.as_posix()}{FileExtensions.MD5}")

    # WHEN extracting the md5 sum
    extracted_sum: str = extract_md5sum(md5sum_file=md5sum_file)

    # THEN the function should return a string with the md5 sum
    assert isinstance(extracted_sum, str)


@pytest.mark.parametrize(
    "file_fixture, expected",
    [("fastq_file", True), ("fastq_file_father", False), ("non_existing_file_path", False)],
    ids=["Existing correct file", "Existing incorrect file", "Non existing file"],
)
def test_is_md5sum_correct(file_fixture: str, expected: bool, request: pytest.FixtureRequest):
    """Test that the function correctly checks if the md5sum is correct."""
    # GIVEN a file
    file_path: Path = request.getfixturevalue(file_fixture)

    # WHEN checking if the md5sum is correct
    is_correct: bool = is_md5sum_correct(file_path)

    # THEN a teh result is expected
    assert is_correct == expected
