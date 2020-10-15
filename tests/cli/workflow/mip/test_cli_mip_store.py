"""This script tests the cli mip store functions"""
import logging

from cg.cli.workflow.mip.store import analysis, completed


def test_store_no_config(cli_runner, mip_store_context, caplog):
    """Test the function to check for config files"""
    # GIVEN the cli function
    caplog.set_level(logging.INFO)
    # WHEN we run store analysis on no config
    result = cli_runner.invoke(analysis, obj=mip_store_context)
    # THEN We should be informed to enter a config file
    assert "Provide a config file." in caplog.text
    # THEN the exit code should be EXIT_FAIL
    assert result.exit_code == 1


def test_store_analysis(
    cli_runner, mip_configs: dict, mip_store_context, mip_qc_sample_info: dict, project_dir, caplog
):
    """Test if store completed stores a completed sample"""
    # GIVEN a cli function
    caplog.set_level(logging.INFO)
    # WHEN we run store on a config
    result = cli_runner.invoke(analysis, [str(mip_configs["yellowhog"])], obj=mip_store_context)
    # THEN we should store the files in housekeeper
    assert "included files in Housekeeper" in result.output
    assert "new bundle added: yellowhog" in caplog.text
    # THEN the exit code should be EXIT_SUCCESS
    assert result.exit_code == 0


def test_store_completed(cli_runner, mip_store_context, mip_case_ids: dict, caplog):
    """Test if store completed stores function"""
    # GIVEN a cli function
    caplog.set_level(logging.INFO)
    # WHEN we run store all completed cases
    result = cli_runner.invoke(completed, obj=mip_store_context)
    # THEN command is run successfully
    for case in mip_case_ids:
        assert f"storing family: {case}" in result.output
    # THEN some cases should be added and some should fail
    assert "new bundle added: yellowhog" in caplog.text
    assert "case storage failed: purplesnail" in caplog.text
    assert "new bundle added: bluezebra" in caplog.text
    assert "included files in Housekeeper" in result.output
    # THEN the command should have an EXIT_FAIL code
    assert result.exit_code == 1
