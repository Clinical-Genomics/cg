from cg.meta.report.field_validators import get_missing_report_data, update_missing_data_dict


def test_get_missing_report_data(report_api_mip_dna, case_mip_dna):
    """Checks the empty and missing report fields retrieval"""

    # GIVEN a report data model and a list of required MIP DNA report fields
    report_data = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )
    required_fields = report_api_mip_dna.get_required_fields()

    # GIVEN some allowed empty fields
    report_data.version = None
    report_data.customer.id = None
    report_data.case.samples[0].methods.library_prep = None

    # GIVEN some required empty fields
    report_data.accredited = None
    report_data.case.samples[0].metadata.million_read_pairs = None
    report_data.case.samples[1].metadata.duplicates = None

    # WHEN retrieving the missing data
    missing_fields, empty_fields = get_missing_report_data(report_data, required_fields)

    # THEN assert that the empty fields are discretised between missing and allowed empty categories
    # Empty required fields
    assert "accredited" in missing_fields["report"]
    assert "million_read_pairs" in missing_fields["metadata"]["ADM1"]
    assert "duplicates" in missing_fields["metadata"]["ADM2"]

    # Empty allowed fields
    assert "version" in empty_fields["report"]
    assert "id" in empty_fields["customer"]
    assert "library_prep" in empty_fields["methods"]["ADM1"]


def test_update_missing_data_dict():
    """Verifies nested append to a missing dictionary"""

    # GIVEN a missing report data dictionary
    missing_data = {
        "report": "accredited",
        "metadata": {"sample_1": "million_read_pairs", "sample_2": "duplicates"},
    }

    # WHEN appending a new (nested) key value
    update_missing_data_dict(missing_data=missing_data, source="customer", field="name")
    update_missing_data_dict(
        missing_data=missing_data, source="applications", field="tag", label="app_1"
    )

    # WHEN appending a field to an existing source
    update_missing_data_dict(missing_data=missing_data, source="report", field="version")

    # WHEN appending a field to an existing nested source
    update_missing_data_dict(
        missing_data=missing_data, source="metadata", field="pct_10x", label="sample_2"
    )

    # THEN check if the added data is correctly appended and formatted
    assert "name" in missing_data["customer"]
    assert "tag" in missing_data["applications"]["app_1"]
    assert "version" in missing_data["report"]
    assert "pct_10x" in missing_data["metadata"]["sample_2"]
