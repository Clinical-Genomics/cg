from pathlib import Path

import pytest

from cg.meta.workflow.fastq import FastqHandler


@pytest.mark.parametrize(
    "fastq_header, expected_header_meta",
    [
        (
            "@HWUSI-EAS100R:6:73:941:1973#0/1",
            {"lane": 6, "flow_cell": "XXXXXX", "read_number": 1},
        ),
        (
            "@EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG",
            {"lane": 2, "flow_cell": "FC706VJ", "read_number": 1},
        ),
        (
            "@ST-E00201:173:HCLCGALXX:1:2106:22516:34834/1",
            {"lane": 1, "flow_cell": "HCLCGALXX", "read_number": 1},
        ),
    ],
)
def test_parse_fastq_header(fastq_header: str, expected_header_meta: dict, fixtures_dir):
    # GIVEN a FASTQ header

    # WHEN parsing header
    header_meta = FastqHandler.parse_fastq_header(line=fastq_header)

    # THEN
    assert header_meta == expected_header_meta


@pytest.mark.parametrize(
    "fastq_path, expected_fastq_meta",
    [
        (
            Path("tests", "fixtures", "io", "casava_five_parts.fastq.gz"),
            {
                "path": Path("tests", "fixtures", "io", "casava_five_parts.fastq.gz"),
                "lane": 6,
                "flowcell": "XXXXXX",
                "read": 1,
                "undetermined": None,
            },
        ),
        (
            Path("tests", "fixtures", "io", "casava_ten_parts.fastq.gz"),
            {
                "path": Path("tests", "fixtures", "io", "casava_ten_parts.fastq.gz"),
                "lane": 2,
                "flowcell": "FC706VJ",
                "read": 1,
                "undetermined": None,
            },
        ),
        (
            Path("tests", "fixtures", "io", "casava_seven_parts.fastq.gz"),
            {
                "path": Path("tests", "fixtures", "io", "casava_seven_parts.fastq.gz"),
                "lane": 1,
                "flowcell": "HCLCGALXX",
                "read": 1,
                "undetermined": None,
            },
        ),
    ],
)
def test_parse_file_data(fastq_path: Path, expected_fastq_meta: dict, mocker):
    # GIVEN a FASTQ file

    mocker.patch("cg.meta.workflow.fastq._is_undetermined_in_path", return_value=None)
    # WHEN parsing header
    header_meta = FastqHandler.parse_file_data(fastq_path=fastq_path)

    # THEN
    assert header_meta == expected_fastq_meta
