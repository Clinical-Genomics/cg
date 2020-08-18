""" Test the CLI for run mip-dna """
import logging

from cg.cli.workflow.mip_dna.base import run
from cg.apps.mip import MipAPI

CASE_ID = "yellowhog"
CONDA_ENV = "S_mip_rd-dna"
EMAIL = "james.holden@scilifelab.se"


def test_cg_dry_run(cli_runner, tb_api, analysis_store_single_case, caplog):
    """Test print the MIP run to console"""
    # GIVEN a cli function

    context = {}
    context["db"] = analysis_store_single_case
    context["tb"] = tb_api
    context["dna_api"] = MipAPI("${HOME}/bin/mip", "analyse rd_dna", CONDA_ENV)
    context["mip-rd-dna"] = {"mip_config": "config.yaml"}

    # WHEN we run a case in dry run mode
    caplog.set_level(logging.INFO)
    cli_runner.invoke(run, ["--dry-run", "--email", EMAIL, CASE_ID], obj=context)

    # THEN the command should be printed
    with caplog.at_level(logging.INFO):
        assert (
            "${HOME}/bin/mip analyse rd_dna yellowhog --config config.yaml "
            "--slurm_quality_of_service normal --email james.holden@scilifelab.se" in caplog.text
        )


def test_run(cli_runner, tb_api, analysis_store_single_case, caplog, monkeypatch):
    """Test run MIP DNA analysis"""

    def mip_run(_self, **kwargs):
        """monkeypatch function so we don't actually run MIP"""
        del kwargs

    # GIVEN a cli function
    context = {}
    monkeypatch.setattr(MipAPI, "run", mip_run)
    mip_api = MipAPI("${HOME}/bin/mip", "analyse rd_dna", CONDA_ENV)
    context["db"] = analysis_store_single_case
    context["tb"] = tb_api
    context["dna_api"] = mip_api
    context["mip-rd-dna"] = {"mip_config": "config.yaml"}

    # WHEN we run a case
    caplog.set_level(logging.INFO)
    cli_runner.invoke(run, ["--email", EMAIL, CASE_ID], obj=context)

    # THEN we should get to the end of the function
    with caplog.at_level(logging.INFO):
        assert "MIP rd-dna run started!" in caplog.text

    # WHEN we run a case in MIP dry mode
    caplog.set_level(logging.INFO)
    cli_runner.invoke(run, ["--mip-dry-run", "--email", EMAIL, CASE_ID], obj=context)

    # THEN we should get to the end of the function
    with caplog.at_level(logging.INFO):
        assert "MIP rd-dna run started!" in caplog.text
