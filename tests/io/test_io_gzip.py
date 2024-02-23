from pathlib import Path

from cg.io.gzip import read_gzip_first_line


def test_read_gzip_first_line(gzip_file_path: Path):
    """
    Test reading first line from a gzip file into a string.
    """
    # GIVEN a gzip file

    # WHEN reading the file
    line: str = read_gzip_first_line(file_path=gzip_file_path)

    # THEN assert a str is returned
    assert isinstance(line, str)

    # THEN the content should match the expected line
    assert line == "- ipsum, sit, amet"
