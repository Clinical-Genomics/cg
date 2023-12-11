import pytest

from cg.meta.workflow.fastq import FastqHandler


@pytest.mark.parametrize(
    "fastq_header, expected_header_meta",
    [
        (
            "@HWUSI-EAS100R:6:73:941:1973#0/1",
            {"lane": str(6), "flowcell": "XXXXXX", "readnumber": str(1)},
        ),
        (
            "@EAS139:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG",
            {"lane": str(2), "flowcell": "FC706VJ", "readnumber": str(1)},
        ),
        (
            "@ST-E00201:173:HCLCGALXX:1:2106:22516:34834/1",
            {"lane": str(1), "flowcell": "HCLCGALXX", "readnumber": str(1)},
        ),
    ],
)
def test_parse_fastq_header(fastq_header: str, expected_header_meta: dict):
    # GIVEN a FASTQ header

    # WHEN parsing header
    header_meta = FastqHandler.parse_fastq_header(line=fastq_header)

    # THEN
    assert header_meta == expected_header_meta
