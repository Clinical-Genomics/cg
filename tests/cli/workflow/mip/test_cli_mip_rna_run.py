""" Test the CLI for run mip-rna """
import logging

from cg.cli.workflow.mip_rna.base import run


def test_cg_dry_run(cli_runner, caplog, case_id, email_adress, rna_mip_context):
    """Test print the MIP command to console"""

    caplog.set_level(logging.INFO)
    # GIVEN a cli function
    rna_mip_context["analysis_api"].get_pedigree_config_path(case_id=case_id).parent.mkdir(
        parents=True, exist_ok=True
    )
    rna_mip_context["analysis_api"].get_pedigree_config_path(case_id=case_id).touch(exist_ok=True)
    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(
        run, ["--dry-run", "--email", email_adress, case_id], obj=rna_mip_context
    )

    # THEN the command should be printed
    assert result.exit_code == 0
    assert f"analyse rd_rna {case_id} --config config.yaml --email {email_adress}" in caplog.text
