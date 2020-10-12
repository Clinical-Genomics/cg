"""Test the cli for uploading to scout"""
import logging

from cg.cli.upload.base import scout


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
    base_context, scout_load_config, upload_scout_api, cli_runner, caplog
):
    """Test to upload a case to scout using a load config"""
    # GIVEN a case with a scout load config in housekeeper
    case_id = base_context["status_db"].families().first().internal_id
    tag_name = upload_scout_api.get_load_config_tag()

    base_context["housekeeper_api"].add_file(
        path=scout_load_config, version_obj=None, tags=tag_name
    )
    load_config_file = base_context["housekeeper_api"].get_files(case_id, [tag_name])[0]
    assert load_config_file

    def case_exists_in_status(case_id, store):
        """Check if case exists in status database"""
        return store.families().first().internal_id == case_id

    assert case_exists_in_status(case_id, base_context["status_db"])

    # WHEN invoking command to upload case to scout
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(scout, [case_id], obj=base_context)

    # THEN assert that the case was loaded succesfully
    def case_loaded_succesfully(caplog):
        """Check output that case was loaded"""
        return check_log(caplog, string="Case loaded successfully to Scout")

    assert case_loaded_succesfully(caplog)

    # THEN assert that the load config was used
    def load_file_mentioned_in_result(result, load_config_file):
        """Check output that load file is mentioned"""
        return load_config_file in result.output

    assert load_file_mentioned_in_result(result, load_config_file.full_path)


def test_produce_load_config(base_context, cli_runner, case_id, scout_hk_bundle_data, helpers):
    """Test create a scout load config with the scout upload api"""
    # GIVEN a singleton WGS case

    base_context["scout_upload_api"].mock_generate_config = False
    # GIVEN a housekeeper instance with some bundle information
    hk_mock = base_context["housekeeper_api"]
    helpers.ensure_hk_bundle(hk_mock, scout_hk_bundle_data)

    # WHEN running cg upload scout -p <caseid>
    result = cli_runner.invoke(scout, [case_id, "--print"], obj=base_context)
    # THEN assert mother: '0' and father: '0'
    assert "'mother': '0'" in result.output
    assert "'father': '0'" in result.output
    assert "'delivery_report'" in result.output


def test_produce_load_config_no_delivery(
    base_context, cli_runner, analysis_family_single_case, scout_hk_bundle_data, helpers
):
    """Test to produce a load config without a delivery report"""
    # GIVEN a singleton WGS case

    base_context["scout_upload_api"].mock_generate_config = False
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
    base_context["scout_upload_api"].mock_generate_config = False

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
    assert isinstance(result.exception, FileNotFoundError)


def test_upload_scout_cli_file_exists(base_context, cli_runner, caplog, case_id):
    """Test to upload a case when the load config already exists"""
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    # GIVEN that the upload file already exists
    config = {"dummy": "data"}
    base_context["scout_upload_api"].config = config
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
    config = {"dummy": "data"}
    tag_name = base_context["scout_upload_api"].get_load_config_tag()
    base_context["scout_upload_api"].config = config
    base_context["housekeeper_api"].add_file(
        path=scout_load_config, version_obj=None, tags=tag_name
    )
    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id], obj=base_context)

    # THEN assert that the call exits without errors
    assert result.exit_code == 0


def test_upload_scout_cli_print_console(base_context, cli_runner, case_id):
    """Test to dry run a case upload"""
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    config = {"dummy": "data"}
    base_context["scout_upload_api"].config = config
    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id, "--print"], obj=base_context)

    # THEN assert that the call exits without errors
    assert result.exit_code == 0

    assert "dummy" in result.output
