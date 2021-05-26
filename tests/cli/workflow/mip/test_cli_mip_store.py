"""This script tests the cli mip store functions"""
import logging

from cg.cli.workflow.mip.store import analysis
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from click.testing import CliRunner


def test_store_no_config(cli_runner: CliRunner, dna_mip_context: CGConfig, caplog):
    """Test the function to check for config files"""

    caplog.set_level(logging.INFO)
    # WHEN we run store analysis on no config
    result = cli_runner.invoke(analysis, obj=dna_mip_context)
    # THEN We should be informed to enter a config file
    assert "Provide a config file." in caplog.text
    # THEN the exit code should be EXIT_FAIL
    assert result.exit_code == EXIT_FAIL


def test_store_analysis_exception(
    cli_runner: CliRunner, dna_mip_context: CGConfig, mip_configs: dict, caplog
):
    """Test that the analysis function enters the exception clause"""
    with caplog.at_level("ERROR", "INFO"):
        # WHEN we run store on a case without deliverables
        result = cli_runner.invoke(analysis, [str(mip_configs["purplesnail"])], obj=dna_mip_context)
        # THEN we should be informed that mandatory files are missing
        assert "Mandatory files are missing" in caplog.text
        # THEN we should not include any files in housekeeper
        assert "included files in Housekeeper" not in caplog.text
        # THEN the exit code should be EXIT_FAIL
        assert result.exit_code == EXIT_FAIL


def test_store_analysis(
    cli_runner: CliRunner,
    mip_configs: dict,
    dna_mip_context: CGConfig,
    mip_qc_sample_info: dict,
    caplog,
):
    """Test if store completed stores a completed sample"""

    with caplog.at_level("INFO"):
        # WHEN we run store on a config
        result = cli_runner.invoke(analysis, [str(mip_configs["yellowhog"])], obj=dna_mip_context)
        # THEN we should store the files in housekeeper
        assert "new bundle added: yellowhog" in caplog.text
        assert "Included files in Housekeeper" in caplog.text
        # THEN the exit code should be EXIT_SUCCESS
        assert result.exit_code == EXIT_SUCCESS
