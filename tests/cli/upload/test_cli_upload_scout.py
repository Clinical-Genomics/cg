import logging
import pytest

from cg.cli.upload import scout

def test_upload_scout_cli_file_exists(base_context, cli_runner, caplog):
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    # GIVEN that the upload file already exists
    config = {'dummy': 'data'}
    base_context['scout_upload_api'].config = config
    base_context['scout_upload_api'].file_exists = True
    case_id = 'dummy_case_id'
    # WHEN uploading a case with the cli and printing the upload config
    result = cli_runner.invoke(scout, [case_id], obj=base_context)
    
    # THEN assert that the call exits without errors
    assert result.exit_code == 0
    # THEN assert that a warning is logged
    warned = False
    for _, level, message in caplog.record_tuples:
        if level == logging.WARNING:
            warned = True
    assert warned

def test_upload_scout_cli(base_context, cli_runner):
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    # WHEN uploading a case with the cli and printing the upload config
    config = {'dummy': 'data'}
    base_context['scout_upload_api'].config = config
    case_id = 'dummy_case_id'
    result = cli_runner.invoke(scout, [case_id], obj=base_context)
    
    # THEN assert that the call exits without errors
    assert result.exit_code == 0


def test_upload_scout_cli_print_console(base_context, cli_runner):
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    # WHEN uploading a case with the cli and printing the upload config
    config = {'dummy': 'data'}
    base_context['scout_upload_api'].config = config
    case_id = 'dummy_case_id'
    result = cli_runner.invoke(scout, [case_id, '--print'], obj=base_context)
    
    # THEN assert that the call exits without errors
    assert result.exit_code == 0
    
    assert 'dummy' in result.output
    