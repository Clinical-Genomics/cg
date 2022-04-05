"""Tests report data validation"""

from cg.meta.report.field_validators import get_missing_report_data, get_empty_report_data


def test_get_empty_report_data(report_api_mip_dna, case_mip_dna):
    """Tests the empty report fields retrieval"""

    # GIVEN a report data model
    report_data = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )
    # GIVEN some empty fields
    report_data.version = None
    report_data.accredited = None
    report_data.customer.id = "N/A"
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
    assert "library_prep" in empty_fields["methods"]["ADM1"]
    assert "million_read_pairs" in empty_fields["metadata"]["ADM1"]
    assert "duplicates" in empty_fields["metadata"]["ADM1"]
    assert "duplicates" in empty_fields["metadata"]["ADM2"]


def test_get_missing_report_data(report_api_mip_dna):
    """Checks the missing report fields retrieval"""

    # GIVEN a dictionary of report empty fields and a list of required MIP DNA report fields
    empty_fields = {
        "report": ["version", "accredited"],
        "customer": ["id"],
        "methods": {"ADM1": ["library_prep"]},
        "metadata": {"ADM1": ["million_read_pairs", "duplicates"], "ADM2": ["duplicates"]},
    }

    required_fields = report_api_mip_dna.get_required_fields()

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
