""" Test the CLI for run mip-rna """
import logging

from cg.cli.workflow.mip_rna.base import run
from cg.apps.mip import MipAPI


def test_run_dry(cli_runner, tb_api, mock_store, caplog):
    """Test run MIP RNA analysis"""
    # GIVEN a cli function

    context = {}
    context["db"] = mock_store
    context["tb"] = tb_api
    context["rna_api"] = MipAPI("${HOME}/bin/mip", "analyse rd_rna", "S_mip8.2_rd-rna")
    context["mip-rd-rna"] = {"mip_config": "config.yaml"}

    # WHEN we run a case in dry run mode
    caplog.set_level(logging.INFO)
    cli_runner.invoke(
        run, ["--dry", "--email", "james.holden@scilifelab.se", "angrybird"], obj=context
    )

    # THEN the command should be printed
    with caplog.at_level(logging.INFO):
        assert (
            "${HOME}/bin/mip analyse rd_rna angrybird --config_file config.yaml "
            "--email james.holden@scilifelab.se --dry_run_all" in caplog.text
        )


def test_run(cli_runner, tb_api, mock_store, caplog, monkeypatch):
    """Test run MIP RNA analysis"""

    def mip_run(_self, **kwargs):
        """monkeypatch function so we don't actually run MIP"""
        del kwargs

    # GIVEN a cli function
    context = {}
    monkeypatch.setattr(MipAPI, "run", mip_run)
    mip_api = MipAPI("${HOME}/bin/mip", "analyse rd_rna", "S_mip8.2_rd-rna")
    context["db"] = mock_store
    context["tb"] = tb_api
    context["rna_api"] = mip_api
    context["mip-rd-rna"] = {"mip_config": "config.yaml"}

    # WHEN we run a case
    caplog.set_level(logging.INFO)
    cli_runner.invoke(run, ["--email", "james.holden@scilifelab.se", "angrybird"], obj=context)

    # THEN we should get to the end of the function
    with caplog.at_level(logging.INFO):
        assert "MIP run started!" in caplog.text
