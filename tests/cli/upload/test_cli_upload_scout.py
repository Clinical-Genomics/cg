"""Test the cli for uploading to scout"""
import logging

from cg.cli.upload.upload import scout

def test_upload_with_load_config(hk_api, upload_scout_api, analysis_store_single_case, 
    analysis_family_single_case):
    # GIVEN a case with a scout load config in housekeeper
    case_id = analysis_store_single_case.families().first().internal_id
    tag_name = upload_scout_api.get_load_config_tag()
    
    load_config_file = hk_api.get_files(case_id, [tag_name])[0]
    assert load_config_file
    assert case_exists_in_status(case_id, store)
    assert the_case_has_parent_not_in_the_file(case_id, load_file)
    
    # WHEN invoking command to upload case to scout
    result = cli_runner.invoke(scout, [case_id, ''], obj=base_context)
    
    # THEN the file was used to upload to scout
    assert file_was_used_in_the_upload(load_file)
    # THEN assert that the changes made in status is not transered to scout
    assert scout_case_lacks_parent_not_in_the_file(parent)    
    
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
    warned = False
    for _, level, message in caplog.record_tuples:
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
