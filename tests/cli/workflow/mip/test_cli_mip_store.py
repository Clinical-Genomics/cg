"""This script tests the cli mip store functions"""
import logging

from click.testing import CliRunner

from cg.cli.workflow.mip.store import analysis, completed
from cg.constants import EXIT_FAIL, EXIT_SUCCESS


def test_store_no_config(cli_runner: CliRunner, mip_store_context: dict, caplog):
    """Test the function to check for config files"""

    caplog.set_level(logging.INFO)
    # WHEN we run store analysis on no config
    result = cli_runner.invoke(analysis, obj=mip_store_context)
    # THEN We should be informed to enter a config file
    assert "Provide a config file." in caplog.text
    # THEN the exit code should be EXIT_FAIL
    assert result.exit_code == EXIT_FAIL


def test_store_analysis_exception(
    cli_runner: CliRunner, mip_store_context: dict, mip_configs: dict
):
    """Test that the analysis function enters the exception clause"""

    # WHEN we run store on a case without deliverables
    result = cli_runner.invoke(analysis, [str(mip_configs["purplesnail"])], obj=mip_store_context)
    # THEN we should be informed that mandatory files are missing
    assert "Mandatory files are missing" in result.output
    # THEN we should not include any files in housekeeper
    assert "included files in Housekeeper" not in result.output
    # THEN the exit code should be EXIT_FAIL
    assert result.exit_code == EXIT_FAIL


def test_store_analysis(
    cli_runner: CliRunner,
    mip_configs: dict,
    mip_store_context: dict,
    mip_qc_sample_info: dict,
    caplog,
):
    """Test if store analysis stores a completed sample"""

    # GIVEN analysis has not yet been stored
    assert not mip_store_context["db"].family("yellowhog").analyses
    caplog.set_level(logging.INFO)

    # WHEN we run store on a config
    result = cli_runner.invoke(analysis, [str(mip_configs["yellowhog"])], obj=mip_store_context)

    # THEN it should output that it has stored the files in housekeeper
    assert "new bundle added: yellowhog" in caplog.text
    assert "included files in Housekeeper" in result.output

    # THEN the exit code should be EXIT_SUCCESS
    assert result.exit_code == EXIT_SUCCESS


def test_store_completed_good_cases(
    cli_runner: CliRunner, mip_store_context: dict, mip_case_ids: dict, caplog
):
    """Test if store completed stores function"""

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
    assert result.exit_code == EXIT_FAIL
