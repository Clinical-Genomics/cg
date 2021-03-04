"""This script tests the cli mip store functions"""
import logging
from pathlib import Path

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.cli.workflow.mip.store import analysis, completed
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from click.testing import CliRunner

from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI


def test_store_no_config(cli_runner: CliRunner, dna_mip_context: dict, caplog):
    """Test the function to check for config files"""

    caplog.set_level(logging.INFO)
    # WHEN we run store analysis on no config
    result = cli_runner.invoke(analysis, obj=dna_mip_context)
    # THEN We should be informed to enter a config file
    assert "Provide a config file." in caplog.text
    # THEN the exit code should be EXIT_FAIL
    assert result.exit_code == EXIT_FAIL


def test_store_analysis_exception(
    cli_runner: CliRunner, dna_mip_context: dict, mip_configs: dict, caplog
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
    dna_mip_context: dict,
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


def test_store_completed_good_cases(
    cli_runner: CliRunner,
    mocker,
    dna_mip_context: dict,
    context_config,
    mip_case_ids: dict,
    mip_configs,
    helpers,
    caplog,
):
    """Test if store completed stores function"""

    caplog.set_level("INFO")

    mocker.patch.object(MipDNAAnalysisAPI, "get_case_config_path")
    MipDNAAnalysisAPI.get_case_config_path.return_value = Path(
        "tests/fixtures/apps/mip/dna/store/case_config.yaml"
    )

    mocker.patch.object(TrailblazerAPI, "get_latest_analysis")
    TrailblazerAPI.get_latest_analysis.return_value = TrailblazerAnalysis.parse_obj(
        {
            "id": 1,
            "family": "yellowhog",
            "status": "completed",
        }
    )

    status_db = dna_mip_context["analysis_api"].status_db
    for case_id in ["yellowhog", "bluezebra", "purplesnail"]:
        case_obj = status_db.family(case_id)
        if not case_obj:
            case_obj = helpers.add_case(store=status_db, internal_id=case_id)
        case_obj.action = "running"
        status_db.commit()
    # WHEN we run store all completed cases
    result = cli_runner.invoke(completed, obj=dna_mip_context)
    # THEN some cases should be added and some should fail
    assert "new bundle added: yellowhog" in caplog.text
    assert "Case storage failed: purplesnail" in caplog.text
    assert "new bundle added: bluezebra" in caplog.text
    assert "Included files in Housekeeper" in caplog.text
    # THEN the command should have an EXIT_FAIL code
    assert result.exit_code == EXIT_FAIL
