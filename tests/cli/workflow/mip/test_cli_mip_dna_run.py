""" Test the CLI for run mip-dna """
import logging

from cg.cli.workflow.mip_dna.base import run


def test_cg_dry_run(cli_runner, caplog, case_id, email_adress, dna_mip_context):
    """Test print the MIP run to console"""

    caplog.set_level(logging.INFO)
    dna_mip_context["analysis_api"].get_pedigree_config_path(case_id=case_id).parent.mkdir(
        parents=True, exist_ok=True
    )
    dna_mip_context["analysis_api"].get_pedigree_config_path(case_id=case_id).touch(exist_ok=True)
    # GIVEN a cli function
    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(
        run, ["--dry-run", "--email", email_adress, case_id], obj=dna_mip_context
    )
    # THEN command is run successfully
    assert result.exit_code == 0

    # THEN the command should be printed
    assert (
        f"analyse rd_dna {case_id} --config config.yaml --slurm_quality_of_service normal --email {email_adress}"
        in caplog.text
    )
