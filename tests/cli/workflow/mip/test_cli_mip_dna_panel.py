""" Test the CLI for mip-dna panel"""

from cg.cli.workflow.mip_dna.base import panel


def test_cg_workflow_mip_dna_panel(cli_runner, case_id, mip_dna_context):
    """Test print the MIP dna panel command to console"""

    # GIVEN a cli function

    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(panel, [case_id], obj=mip_dna_context)

    # THEN the command should be printed
    assert result.exit_code == 0
