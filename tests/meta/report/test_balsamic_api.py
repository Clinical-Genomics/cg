import copy


def test_is_report_accredited(report_api_balsamic, case_id):
    """Test report accreditation for a specific BALSAMIC analysis."""

    # GIVEN a mock metadata object and an accredited one
    balsamic_metadata = report_api_balsamic.analysis_api.get_latest_metadata(case_id)

    balsamic_accredited_metadata = copy.deepcopy(balsamic_metadata)
    balsamic_accredited_metadata.config.panel.capture_kit = "gmsmyeloid"

    # WHEN performing the accreditation validation
    unaccredited_report = report_api_balsamic.is_report_accredited(None, balsamic_metadata)
    accredited_report = report_api_balsamic.is_report_accredited(None, balsamic_accredited_metadata)

    # THEN verify that only the panel "gmsmyeloid" reports are validated
    assert not unaccredited_report
    assert accredited_report
