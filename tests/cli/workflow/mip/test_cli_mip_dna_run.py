""" Test the CLI for run mip-dna """
import logging
import os
from pathlib import Path

from cg.cli.workflow.mip_dna.base import run

CASE_ID = "yellowhog"
CONDA_ENV = "S_mip_rd-dna"
EMAIL = "james.holden@scilifelab.se"


def test_cg_dry_run(cli_runner, mip_context, caplog):
    """Test print the MIP run to console"""
    pedigree_path = mip_context.get("dna_api").get_pedigree_config_path(case_id="yellowhog")
    Path.mkdir(pedigree_path.parent, parents=True, exist_ok=True)
    os.link("tests/fixtures/apps/mip/dna/store/pedigree.yaml", pedigree_path)

    # GIVEN a cli function
    with caplog.at_level(logging.INFO):
        # WHEN we run a case in dry run mode
        result = cli_runner.invoke(run, ["--dry-run", "--email", EMAIL, CASE_ID], obj=mip_context)

        # THEN the command should be printed
        assert (
            "analyse rd_dna yellowhog --config config.yaml "
            "--slurm_quality_of_service normal --email james.holden@scilifelab.se" in caplog.text
        )
        # THEN command is run successfully
        assert result.exit_code == 0
