""" Test the CLI for run mip-dna """
import logging
from pathlib import Path

from cg.cli.workflow.mip_dna.base import run


def test_cg_dry_run(cli_runner, mip_context, caplog, case_id, email_adress):
    """Test print the MIP run to console"""

    caplog.set_level(logging.INFO)

    pedigree_path = mip_context.get("dna_api").get_pedigree_config_path(case_id=case_id)
    Path.mkdir(pedigree_path.parent, parents=True, exist_ok=True)
    pedigree_file_fixture = Path("tests/fixtures/apps/mip/dna/store/pedigree.yaml")
    pedigree_file_fixture.link_to(pedigree_path)

    # GIVEN a cli function
    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(
        run, ["--dry-run", "--email", email_adress, case_id], obj=mip_context
    )

    # THEN the command should be printed
    assert (
        f"analyse rd_dna {case_id} --config config.yaml --slurm_quality_of_service normal --email {email_adress}"
        in caplog.text
    )

    # THEN command is run successfully
    assert result.exit_code == 0
