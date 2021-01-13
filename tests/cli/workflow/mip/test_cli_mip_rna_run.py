""" Test the CLI for run mip-rna """
import logging

from cg.cli.workflow.mip_rna.base import run


def test_cg_dry_run(cli_runner, tb_api, mip_context, caplog, case_id, email_adress):
    """Test print the MIP command to console"""

    caplog.set_level(logging.INFO)
    # GIVEN a cli function

    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(
        run, ["--dry-run", "--email", email_adress, case_id], obj=mip_context
    )

    # THEN the command should be printed
    assert result.exit_code == 0
    assert f"analyse rd_rna {case_id} --config config.yaml --email {email_adress}" in caplog.text
