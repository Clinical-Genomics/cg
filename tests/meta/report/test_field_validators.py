"""Tests report data validation"""

from cg.meta.report.field_validators import (
    get_missing_report_data,
    get_empty_report_data,
    get_million_read_pairs,
)


def test_get_empty_report_data(report_api_mip_dna, case_mip_dna):
    """Tests the empty report fields retrieval."""

    # GIVEN a report data model
    report_data = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )

    # GIVEN some empty fields
    report_data.version = None
    report_data.accredited = None
    report_data.customer.id = "N/A"
    report_data.customer.scout_access = False
    report_data.case.samples[0].methods.library_prep = ""
    report_data.case.samples[0].metadata.million_read_pairs = None
    report_data.case.samples[0].metadata.duplicates = None
    report_data.case.samples[1].metadata.duplicates = None

    # WHEN retrieving the missing data
    empty_fields = get_empty_report_data(report_data)

    # THEN assert that the empty fields are correctly retrieved
    assert "version" in empty_fields["report"]
    assert "accredited" in empty_fields["report"]
    assert "id" in empty_fields["customer"]
    assert "scout_access" not in empty_fields["customer"]
    assert "library_prep" in empty_fields["methods"]["ADM1"]
    assert "million_read_pairs" in empty_fields["metadata"]["ADM1"]
    assert "duplicates" in empty_fields["metadata"]["ADM1"]
    assert "duplicates" in empty_fields["metadata"]["ADM2"]


def test_get_missing_report_data(report_api_mip_dna, case_mip_dna):
    """Checks the missing report fields retrieval."""

    # GIVEN a report data model
    report_data = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )
    report_data.case.samples[0].application.prep_category = "wgs"  # ADM1 sample (WGS)
    report_data.case.samples[1].application.prep_category = "wes"  # ADM2 sample (WES)

    # GIVEN a dictionary of report empty fields and a list of required MIP DNA report fields
    empty_fields = {
        "report": ["version", "accredited"],
        "customer": ["id"],
        "methods": {"ADM1": ["library_prep"]},
        "metadata": {
            "ADM1": ["bait_set", "million_read_pairs", "duplicates"],
            "ADM2": ["bait_set", "duplicates"],
        },
    }

    required_fields = report_api_mip_dna.get_required_fields(report_data.case)

    # WHEN retrieving the missing data
    missing_fields = get_missing_report_data(empty_fields, required_fields)

    # THEN assert that the required fields are identified
    assert "version" not in missing_fields["report"]
    assert "accredited" in missing_fields["report"]
    assert "customer" not in missing_fields
    assert "methods" not in missing_fields
    assert "million_read_pairs" in missing_fields["metadata"]["ADM1"]
    assert "duplicates" in missing_fields["metadata"]["ADM1"]
    assert "duplicates" in missing_fields["metadata"]["ADM2"]
    assert "bait_set" not in missing_fields["metadata"]["ADM1"]
    assert "bait_set" in missing_fields["metadata"]["ADM2"]
    assert "ADM3" not in missing_fields["metadata"]


def test_get_million_read_pairs():
    """Tests millions read pairs computation."""

    # GIVEN a number os sequencing reads and its representation in millions of read pairs
    sample_reads = 1_200_000_000
    expected_million_read_pairs = 600.0

    # WHEN obtaining the number of reds in millions of read pairs
    million_read_pairs = get_million_read_pairs(sample_reads)

    # THEN the expected value should match the calculated one
    assert million_read_pairs == expected_million_read_pairs


def test_get_million_read_pairs_zero_input():
    """Tests millions read pairs computation when the sample reads number is zero."""

    # GIVEN zero as number of reads
    sample_reads = 0

    # WHEN retrieving the number of reds in millions of read pairs
    million_read_pairs = get_million_read_pairs(sample_reads)

    # THEN the obtained value should be zero
    assert million_read_pairs == 0.0
