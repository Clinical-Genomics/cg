""" Test the CLI for run mip-rna """
import logging

from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.mip_rna.base import run


def test_cg_dry_run(cli_runner, caplog, case_id, email_adress, mip_rna_context, mocker):
    """Test print the MIP command to console"""

    caplog.set_level(logging.INFO)
    # GIVEN a cli function
    # WHEN we run a case in dry run mode

    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing")
    TrailblazerAPI.is_latest_analysis_ongoing.return_value = False

    result = cli_runner.invoke(
        run, ["--dry-run", "--email", email_adress, case_id], obj=mip_rna_context
    )

    # THEN the command should be printed
    assert result.exit_code == 0
