"""Test the cli for uploading to scout"""
import logging

from cg.cli.upload.base import scout


def test_produce_load_config(base_context, cli_runner, analysis_family_single_case):
    # GIVEN a singleton WGS case

    base_context["scout_upload_api"].mock_generate_config = False
    case_id = analysis_family_single_case["internal_id"]

    # WHEN running cg upload scout -p <caseid>
    result = cli_runner.invoke(scout, [case_id, "--print"], obj=base_context)
    # THEN assert mother: '0' and father: '0'
    assert "'mother': '0'" in result.output
    assert "'father': '0'" in result.output
    assert "'delivery_report'" in result.output


def test_produce_load_config_no_delivery(
    base_context, cli_runner, analysis_family_single_case, hk_mock
):
    # GIVEN a singleton WGS case

    base_context["scout_upload_api"].mock_generate_config = False

    # GIVEN a housekeeper that does not return delivery files
    hk_mock.delivery_report = False
    base_context["scout_upload_api"].housekeeper = hk_mock
    assert hk_mock.files(tags=["delivery-report"]).first() is None

    case_id = analysis_family_single_case["internal_id"]

    # WHEN running cg upload scout -p <caseid>
    result = cli_runner.invoke(scout, [case_id, "--print"], obj=base_context)

    # THEN assert the command succeded since delivery report is not mandatory
    assert result.exit_code == 0
    # THEN assert the output has some content
    assert result.output
    # THEN there is no delivery report in the output
    assert "'delivery_report'" not in result.output


def test_produce_load_config_missing_mandatory_file(
    base_context, cli_runner, analysis_family_single_case, hk_mock
):
    # GIVEN a singleton WGS case
    base_context["scout_upload_api"].mock_generate_config = False

    # GIVEN a housekeeper that does not return mandatory files
    hk_mock.missing_mandatory = True
    base_context["scout_upload_api"].housekeeper = hk_mock
    assert hk_mock.files(tags=["vcf-snv-clinical"]).first() is None

    case_id = analysis_family_single_case["internal_id"]

    # WHEN running cg upload scout -p <caseid>
    result = cli_runner.invoke(scout, [case_id, "--print"], obj=base_context)

    # THEN assert the command failed since a mandatory file was missing
    assert result.exit_code != 0
    # THEN assert a FileNotFoundError was raised
    assert isinstance(result.exception, FileNotFoundError)


def test_upload_scout_cli_file_exists(
    base_context, cli_runner, caplog, analysis_family_single_case
):
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    # GIVEN that the upload file already exists
    config = {"dummy": "data"}
    base_context["scout_upload_api"].config = config
    base_context["scout_upload_api"].file_exists = True
    case_id = analysis_family_single_case["internal_id"]

    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id], obj=base_context)

    # THEN assert that the call exits without errors
    assert result.exit_code == 1

    # THEN assert that a warning is logged
    warned = False
    for _, level, _ in caplog.record_tuples:
        if level == logging.WARNING:
            warned = True
    assert warned


def test_upload_scout_cli(base_context, cli_runner, analysis_family_single_case):
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    config = {"dummy": "data"}
    base_context["scout_upload_api"].config = config
    case_id = analysis_family_single_case["internal_id"]
    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id], obj=base_context)

    # THEN assert that the call exits without errors
    assert result.exit_code == 0


def test_upload_scout_cli_print_console(base_context, cli_runner, analysis_family_single_case):
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    config = {"dummy": "data"}
    base_context["scout_upload_api"].config = config
    case_id = analysis_family_single_case["internal_id"]
    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id, "--print"], obj=base_context)

    # THEN assert that the call exits without errors
    assert result.exit_code == 0

    assert "dummy" in result.output
