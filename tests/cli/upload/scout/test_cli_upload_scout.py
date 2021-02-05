"""Test the cli for uploading to scout"""
import logging
from pathlib import Path

from cg.cli.upload.scout import create_scout_load_config, scout
from cg.meta.upload.scout.scout_load_config import ScoutLoadConfig
from cg.meta.upload.scout.scoutapi import UploadScoutAPI
from cg.store import Store
from pydantic import ValidationError
from tests.meta.upload.scout.conftest import fixture_mip_analysis_hk_bundle_data


def check_log(caplog, string=None, warning=None):
    """Parse the log output"""
    found = False
    for _, level, message in caplog.record_tuples:
        if level == logging.WARNING and warning:
            found = True
        if string and string in message:
            found = True
    return found


def test_upload_with_load_config(
    base_context: dict,
    scout_load_config: Path,
    upload_scout_api: UploadScoutAPI,
    cli_runner,
    caplog,
):
    """Test to upload a case to scout using a load config"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a case that exists in status
    case_id = base_context["status_db"].families().first().internal_id
    tag_name = upload_scout_api.get_load_config_tag()
    # GIVEN  that a scout load config exists in housekeeper
    base_context["housekeeper_api"].add_file(
        path=str(scout_load_config), version_obj=None, tags=tag_name
    )
    load_config_file = base_context["housekeeper_api"].get_files(case_id, [tag_name])[0]
    assert load_config_file

    def case_exists_in_status(existing_case_id: str, store: Store):
        """Check if case exists in status database"""
        return store.families().first().internal_id == existing_case_id

    assert case_exists_in_status(case_id, base_context["status_db"])

    # WHEN invoking command to upload case to scout
    with caplog.at_level(logging.DEBUG):
        cli_runner.invoke(scout, [case_id], obj=base_context)

    # THEN assert that the case was loaded succesfully
    def case_loaded_succesfull(caplog):
        """Check output that case was loaded"""
        return check_log(caplog, string="Case loaded successfully to Scout")

    assert case_loaded_succesfull(caplog)

    # THEN assert that the load config was used
    def load_file_mentioned_in_result(caplog, load_config_file: Path):
        """Check output that load file is mentioned"""
        return f"uploaded to scout using load config {load_config_file}" in caplog.text

    assert load_file_mentioned_in_result(caplog, load_config_file.full_path)


def test_produce_load_config(
    base_context: dict, cli_runner, case_id: str, mip_analysis_hk_bundle_data: dict, helpers, caplog
):
    """Test create a scout load config with the scout upload api"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a singleton WGS case
    # GIVEN that the api generates a config
    # GIVEN a housekeeper instance with some bundle information
    hk_mock = base_context["housekeeper_api"]
    helpers.ensure_hk_bundle(hk_mock, mip_analysis_hk_bundle_data)

    # WHEN running cg upload scout -p <caseid>
    result = cli_runner.invoke(create_scout_load_config, [case_id, "--print"], obj=base_context)

    # THEN assert that the call was executed with success
    assert result.exit_code == 0
    # THEN there was some relevant output
    assert "owner" in result.output


def test_produce_load_config_no_delivery(
    base_context, cli_runner, analysis_family_single_case, scout_hk_bundle_data, helpers
):
    """Test to produce a load config without a delivery report"""
    # GIVEN a singleton WGS case

    base_context["scout_upload_api"].config.delivery_report = None
    # GIVEN a populated hk mock
    hk_mock = base_context["housekeeper_api"]
    helpers.ensure_hk_bundle(hk_mock, scout_hk_bundle_data)
    # GIVEN a housekeeper that does not return delivery files
    hk_mock.add_missing_tag("delivery-report")
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
    base_context, cli_runner, case_id, scout_hk_bundle_data, helpers
):
    """Test to produce a load config when mandatory files are missing"""
    # GIVEN a singleton WGS case
    base_context["scout_upload_api"].missing_mandatory_field = True

    # GIVEN a populated hk mock
    hk_mock = base_context["housekeeper_api"]
    helpers.ensure_hk_bundle(hk_mock, scout_hk_bundle_data)
    # GIVEN a housekeeper that does not return mandatory files
    hk_mock.add_missing_tag("vcf-snv-clinical")
    base_context["scout_upload_api"].housekeeper = hk_mock
    assert hk_mock.files(tags=["vcf-snv-clinical"]).first() is None

    # WHEN running cg upload scout -p <caseid>
    result = cli_runner.invoke(scout, [case_id, "--print"], obj=base_context)

    # THEN assert the command failed since a mandatory file was missing
    assert result.exit_code != 0
    # THEN assert a FileNotFoundError was raised
    assert isinstance(result.exception, ValidationError)


def test_upload_scout_cli_file_exists(base_context, cli_runner, caplog, case_id):
    """Test to upload a case when the load config already exists"""
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    assert isinstance(base_context["scout_upload_api"].generate_config("hej"), ScoutLoadConfig)
    # GIVEN that the upload file already exists
    base_context["scout_upload_api"].file_exists = True

    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id], obj=base_context)

    # THEN assert that the call exits without errors
    assert result.exit_code == 1

    # THEN assert that a warning is logged
    warned = check_log(caplog, warning=True)
    assert warned


def test_upload_scout_cli(base_context, cli_runner, case_id, scout_load_config):
    """Test to upload a case to scout using cg upload scout command"""
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    tag_name = base_context["scout_upload_api"].get_load_config_tag()
    base_context["housekeeper_api"].add_file(
        path=scout_load_config, version_obj=None, tags=tag_name
    )
    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id], obj=base_context)

    # THEN assert that the call exits without errors
    assert result.exit_code == 0


def test_upload_scout_cli_print_console(
    base_context, cli_runner, case_id: str, scout_load_object: ScoutLoadConfig, caplog
):
    """Test to dry run a case upload"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    base_context["scout_upload_api"].config = scout_load_object
    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id, "--print"], obj=base_context)

    # THEN assert that the call exits without errors
    assert result.exit_code == 0

    assert case_id in caplog.text
