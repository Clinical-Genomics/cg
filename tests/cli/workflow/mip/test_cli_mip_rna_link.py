""" Test the CLI for mip-rna link"""
import logging

from cg.cli.workflow.mip_rna.base import link


def test_cg_workflow_mip_rna_link(cli_runner, caplog, case_id, mip_rna_context):
    """Test print the MIP rna case config command to console"""

    caplog.set_level(logging.INFO)

    # GIVEN a store with a RNA case with wts application

    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(link, [case_id], obj=mip_rna_context)

    # THEN the command should be printed
    assert result.exit_code == 0
