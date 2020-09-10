""" Test the CLI for run mip-rna """
import logging

from cg.cli.workflow.mip_rna.base import run
from cg.apps.mip import MipAPI

CASE_ID = "yellowhog"
CONDA_ENV = "S_mip_rd-rna"
EMAIL = "james.holden@scilifelab.se"


def test_cg_dry_run(cli_runner, tb_api, analysis_store_single_case, mip_context, caplog):
    """Test print the MIP command to console"""
    # GIVEN a cli function

    # WHEN we run a case in dry run mode
    caplog.set_level(logging.INFO)
    result = cli_runner.invoke(run, ["--dry-run", "--email", EMAIL, CASE_ID], obj=mip_context)

    # THEN the command should be printed
    with caplog.at_level(logging.INFO):
        assert result.exit_code == 0
        assert (
            "analyse rd_rna yellowhog --config config.yaml "
            "--email james.holden@scilifelab.se" in caplog.text
        )


def test_run(cli_runner, tb_api, analysis_store_single_case, caplog, mip_context, monkeypatch):
    """Test run MIP RNA analysis"""

    # GIVEN a cli function

    # WHEN we run a case
    caplog.set_level(logging.INFO)
    cli_runner.invoke(run, ["--email", EMAIL, CASE_ID], obj=mip_context)

    # THEN we should get to the end of the function
    with caplog.at_level(logging.INFO):
        assert "MIP rd-rna run started!" in caplog.text

    # WHEN we run a case in MIP dry mode
    caplog.set_level(logging.INFO)
    cli_runner.invoke(run, ["--mip-dry-run", "--email", EMAIL, CASE_ID], obj=mip_context)

    # THEN we should get to the end of the function
    with caplog.at_level(logging.INFO):
        assert "MIP rd-rna run started!" in caplog.text
