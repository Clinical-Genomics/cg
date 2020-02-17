"""Test the cli for uploading to scout"""
import logging

from cg.cli.upload.upload import scout


def check_log(caplog, string=None, warning=None):
    """Parse the log output"""
    found = False
    for _, level, message in caplog.record_tuples:
        if warning:
            if level == logging.WARNING:
                found = True
        if string:
            if string in message:
                found = True
    return found


def test_upload_with_load_config(
    hk_api,
    upload_scout_api,
    analysis_store_single_case,
    analysis_family_single_case,
    cli_runner,
    base_context,
    caplog,
):
    # GIVEN a case with a scout load config in housekeeper
    case_id = analysis_store_single_case.families().first().internal_id
    tag_name = upload_scout_api.get_load_config_tag()

    load_config_file = hk_api.get_files(case_id, [tag_name])[0]
    assert load_config_file

    def case_exists_in_status(case_id, store):
        """Check if case exists in status database"""
        return store.families().first() != None

    assert case_exists_in_status(case_id, analysis_store_single_case)

    # WHEN invoking command to upload case to scout
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(scout, [case_id], obj=base_context)

    # THEN
    def case_loaded_succesfully(caplog):
        """Check output that case was loaded"""
        return check_log(caplog, string="Case loaded successfully to Scout")

    assert case_loaded_succesfully(caplog)

    def load_file_mentioned_in_result(result, load_config_file):
        """Check output that load file is mentioned"""
        assert load_config_file in result.output

    assert load_file_mentioned_in_result(result)


def test_produce_load_config(base_context, cli_runner, analysis_family_single_case):
    # GIVEN a singleton WGS case

    base_context["scout_upload_api"].mock_generate_config = False
    case_id = analysis_family_single_case["internal_id"]

    # WHEN running cg upload scout -p <caseid>
    result = cli_runner.invoke(scout, [case_id, "--print"], obj=base_context)
    # THEN assert mother: '0' and father: '0'
    assert "'mother': '0'" in result.output
    assert "'father': '0'" in result.output


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
    warned = check_log(caplog, warning=True)
    assert warned


def test_upload_scout_cli(
    base_context, cli_runner, analysis_family_single_case, scout_load_config
):
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    config = {"dummy": "data"}
    base_context["scout_upload_api"].config = config
    base_context["housekeeper_api"].add_file(scout_load_config, None, None)
    case_id = analysis_family_single_case["internal_id"]
    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id], obj=base_context)

    # THEN assert that the call exits without errors
    assert result.exit_code == 0


def test_upload_scout_cli_print_console(
    base_context, cli_runner, analysis_family_single_case
):
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
