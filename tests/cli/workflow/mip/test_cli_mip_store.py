"""This script tests the cli mip store functions"""
import logging

from click.testing import CliRunner

from cg.cli.workflow.mip.store import analysis, completed
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.apps.tb.models import TrailblazerAnalysis


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
    cli_runner: CliRunner, mip_store_context: dict, mip_configs: dict, caplog
):
    """Test that the analysis function enters the exception clause"""
    with caplog.at_level("ERROR", "INFO"):
        # WHEN we run store on a case without deliverables
        result = cli_runner.invoke(
            analysis, [str(mip_configs["purplesnail"])], obj=mip_store_context
        )
        # THEN we should be informed that mandatory files are missing
        assert "Mandatory files are missing" in caplog.text
        # THEN we should not include any files in housekeeper
        assert "included files in Housekeeper" not in caplog.text
        # THEN the exit code should be EXIT_FAIL
        assert result.exit_code == EXIT_FAIL


def test_store_analysis(
    cli_runner: CliRunner,
    mip_configs: dict,
    mip_store_context: dict,
    mip_qc_sample_info: dict,
    caplog,
):
    """Test if store completed stores a completed sample"""

    with caplog.at_level("INFO"):
        # WHEN we run store on a config
        result = cli_runner.invoke(
            analysis, [str(mip_configs["yellowhog"])], obj=mip_store_context, catch_exceptions=False
        )
        # THEN we should store the files in housekeeper
        assert "new bundle added: yellowhog" in caplog.text
        assert "Included files in Housekeeper" in caplog.text
        # THEN the exit code should be EXIT_SUCCESS
        assert result.exit_code == EXIT_SUCCESS


def test_store_completed_good_cases(
    cli_runner: CliRunner, mip_store_context: dict, mip_case_ids: dict, mip_configs, helpers, caplog
):
    """Test if store completed stores function"""

    with caplog.at_level("INFO"):
        trailblazer_api = mip_store_context["trailblazer_api"]
        analyses = [
            {
                "id": 1,
                "family": "yellowhog",
                "config_path": mip_configs["yellowhog"].as_posix(),
                "status": "completed",
            },
            {
                "id": 2,
                "family": "bluezebra",
                "config_path": mip_configs["bluezebra"].as_posix(),
                "status": "completed",
            },
            {
                "id": 3,
                "family": "purplesnail",
                "config_path": mip_configs["purplesnail"].as_posix(),
                "status": "completed",
            },
        ]
        for analysis in analyses:
            trailblazer_api.ensure_get_latest_analysis_response(analysis_dict=analysis)

        status_db = mip_store_context["status_db"]
        for case_id in ["yellowhog", "bluezebra", "purplesnail"]:
            case_obj = status_db.family(case_id)
            if case_obj:
                case_obj.action = "running"
                status_db.commit()
            else:
                helpers.add_family(store=status_db, internal_id=case_id, action="running")

        # WHEN we run store all completed cases
        result = cli_runner.invoke(completed, obj=mip_store_context)
        # THEN some cases should be added and some should fail
        assert "new bundle added: yellowhog" in caplog.text
        assert "Case storage failed: purplesnail" in caplog.text
        assert "new bundle added: bluezebra" in caplog.text
        assert "Included files in Housekeeper" in caplog.text
        # THEN the command should have an EXIT_FAIL code
        assert result.exit_code == EXIT_FAIL
