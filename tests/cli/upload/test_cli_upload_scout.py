import mock

from cg.cli.upload import scout

def test_upload_scout_cli(base_context, cli_runner):
    # GIVEN a case_id where the case exists in status db with at least one analysis
    # GIVEN that the analysis is done and exists in tb
    # WHEN uploading a case with the cli and printing the upload config
    config = {'dummy': 'data'}
    base_context['scout_upload_api'].config = config
    case_id = 'dummy_case_id'
    result = cli_runner.invoke(scout, [case_id], obj=base_context)
    
    # THEN assert that the call exits without errors
    print(result.__dict__)
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
    