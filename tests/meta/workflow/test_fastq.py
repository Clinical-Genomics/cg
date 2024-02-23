from pathlib import Path

import pytest

from cg.meta.workflow.fastq import FastqHandler
from cg.models.fastq import FastqFileMeta


@pytest.mark.parametrize(
    "fastq_header, expected_header_meta",
    [
        (
            "@HWUSI-EAS100R:6:73:941:1973#0/1",
            FastqFileMeta(lane=6, flow_cell_id="XXXXXX", read_direction=1),
        ),
        (
            "@EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG",
            FastqFileMeta(lane=2, flow_cell_id="FC706VJ", read_direction=1),
        ),
        (
            "@ST-E00201:173:HCLCGALXX:1:2106:22516:34834/1",
            FastqFileMeta(lane=1, flow_cell_id="HCLCGALXX", read_direction=1),
        ),
    ],
)
def test_parse_fastq_header(fastq_header: str, expected_header_meta: dict):
    # GIVEN a FASTQ header

    # WHEN parsing header
    header_meta: FastqFileMeta = FastqHandler.parse_fastq_header(line=fastq_header)

    # THEN header meta should match the expected header information
    assert header_meta == expected_header_meta


@pytest.mark.parametrize(
    "fastq_header, expected_error",
    [
        ("no match", TypeError),
        ("no:match", TypeError),
        ("", TypeError),
    ],
)
def test_parse_fastq_header_when_no_match(fastq_header: str, expected_error):
    # GIVEN no matching FASTQ header

    with pytest.raises(expected_error):
        # WHEN parsing header
        # THEN raise error
        FastqHandler.parse_fastq_header(line=fastq_header)


@pytest.mark.parametrize(
    "fastq_path, expected_fastq_meta",
    [
        (
            Path("tests", "fixtures", "io", "casava_five_parts.fastq.gz"),
            FastqFileMeta(
                path=Path("tests", "fixtures", "io", "casava_five_parts.fastq.gz"),
                lane=6,
                flow_cell_id="XXXXXX",
                read_direction=1,
                undetermined=None,
            ),
        ),
        (
            Path("tests", "fixtures", "io", "casava_ten_parts.fastq.gz"),
            FastqFileMeta(
                path=Path("tests", "fixtures", "io", "casava_ten_parts.fastq.gz"),
                lane=2,
                flow_cell_id="FC706VJ",
                read_direction=1,
                undetermined=None,
            ),
        ),
        (
            Path("tests", "fixtures", "io", "casava_seven_parts.fastq.gz"),
            FastqFileMeta(
                path=Path("tests", "fixtures", "io", "casava_seven_parts.fastq.gz"),
                lane=1,
                flow_cell_id="HCLCGALXX",
                read_direction=1,
                undetermined=None,
            ),
        ),
    ],
)
def test_parse_file_data(fastq_path: Path, expected_fastq_meta: dict, mocker):
    # GIVEN a FASTQ file

    with mocker.patch("cg.meta.workflow.fastq._is_undetermined_in_path", return_value=None):
        # WHEN parsing header
        header_meta = FastqHandler.parse_file_data(fastq_path=fastq_path)

        # THEN header meta should match the expected header information
        assert header_meta == expected_fastq_meta
