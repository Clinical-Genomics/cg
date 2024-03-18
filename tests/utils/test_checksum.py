from pathlib import Path

from cg.utils.checksum.checksum import check_md5sum, extract_md5sum


def test_checksum(fastq_file: Path):
    """Tests if the function correctly calculates md5sum and returns the correct result."""
    # GIVEN a fastq file with corresponding correct md5 file

    # THEN a file with a correct md5 sum should return true
    assert check_md5sum(file_path=fastq_file, md5sum="a95cbb265540a2261fce941059784fd1")

    # GIVEN a fastq file with a corresponding incorrect md5 file
    bad_md5sum_file_path: Path = fastq_file.parent.joinpath("fastq_run_R1_001.fastq.gz")

    # THEN a file with an incorrect md5 sum should return false
    assert not check_md5sum(
        file_path=bad_md5sum_file_path, md5sum="c690b0124173772ec4cbbc43709d84ee"
    )


def test_extract_checksum(fastq_file: Path):
    """Tests if the function successfully extract the correct md5sum."""

    # GIVEN a file containing a md5sum
    md5sum_file = Path(f"{fastq_file.as_posix()}.md5")

    # WHEN extracting the md5sum

    # THEN the function should extract it
    assert extract_md5sum(md5sum_file=md5sum_file) == "a95cbb265540a2261fce941059784fd1"
