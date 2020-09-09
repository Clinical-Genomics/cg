""" Test the CLI for run mip-dna """
import logging

from cg.cli.workflow.mip_dna.base import run
from cg.apps.mip import MipAPI

CASE_ID = "yellowhog"
CONDA_ENV = "S_mip_rd-dna"
EMAIL = "james.holden@scilifelab.se"


def test_cg_dry_run(cli_runner, tb_api, analysis_store_single_case, mip_context, caplog):
    """Test print the MIP run to console"""
    # GIVEN a cli function
    with caplog.at_level(logging.INFO):
        # WHEN we run a case in dry run mode
        result = cli_runner.invoke(run, ["--dry-run", "--email", EMAIL, CASE_ID], obj=mip_context)
        # THEN command is run successfully
        assert result.exit_code == 0
        # THEN the command should be printed
        assert (
            "analyse rd_dna yellowhog --config config.yaml "
            "--slurm_quality_of_service normal --email james.holden@scilifelab.se" in caplog.text
        )


def test_run(cli_runner, tb_api, analysis_store_single_case, caplog, monkeypatch, mip_context):
    """Test run MIP DNA analysis"""

    # GIVEN a cli function

    # WHEN we run a case
    caplog.set_level(logging.INFO)
    cli_runner.invoke(run, ["--email", EMAIL, CASE_ID], obj=mip_context)

    # THEN we should get to the end of the function
    with caplog.at_level(logging.INFO):
        assert "MIP rd-dna run started!" in caplog.text

    # WHEN we run a case in MIP dry mode
    caplog.set_level(logging.INFO)
    cli_runner.invoke(run, ["--mip-dry-run", "--email", EMAIL, CASE_ID], obj=mip_context)

    # THEN we should get to the end of the function
    with caplog.at_level(logging.INFO):
        assert "MIP rd-dna run started!" in caplog.text
