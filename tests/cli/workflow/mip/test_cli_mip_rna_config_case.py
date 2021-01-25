""" Test the CLI for mip-rna config-case"""
import logging

from cg.cli.workflow.mip_rna.base import config_case


def test_cg_workflow_mip_rna_config_case_dry_run(cli_runner, caplog, case_id, rna_mip_context):
    """Test print the MIP RNA case config command to console"""

    caplog.set_level(logging.INFO)

    # GIVEN a cli function

    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(config_case, ["--dry-run", case_id], obj=rna_mip_context)

    # THEN the command should be printed
    assert result.exit_code == 0


def test_cg_workflow_mip_rna_config_case(cli_runner, caplog, case_id, rna_mip_context):
    """Test print the MIP rna case config command to file"""

    caplog.set_level(logging.INFO)

    # GIVEN a cli function

    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(config_case, [case_id], obj=rna_mip_context)

    # THEN the command should be printed
    assert result.exit_code == 0
    assert f"Config saved to:" in caplog.text
