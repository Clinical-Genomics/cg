""" Test the CLI for run mip-dna """
import logging
import os
from pathlib import Path

from cg.cli.workflow.mip_dna.base import mip_dna
#from cg.cli.workflow.mip_dna.base import run

CASE_ID = "yellowhog"
EMAIL = "james.holden@scilifelab.se"

def test_mip_dna(cli_runner, mip_context, caplog):
    # GIVEN fastqs are all decompressed and linked
    pedigree_path = mip_context.get("dna_api").get_pedigree_config_path(case_id=CASE_ID)
    Path.mkdir(pedigree_path.parent, parents=True, exist_ok=True)
    os.link("tests/fixtures/apps/mip/dna/store/pedigree.yaml", pedigree_path)

    caplog.set_level(logging.INFO)
    # WHEN calling mip_dna
    result = cli_runner.invoke(mip_dna, ["-c", CASE_ID, "--dry-run"], obj=mip_context, catch_exceptions=False)
    #result = cli_runner.invoke(run, ["--dry-run", CASE_ID], obj=mip_context, catch_exceptions=False)

    # THEN no error should be thrown
    assert result.exit_code == 0
    # THEN should not output "Decompression is running"
    assert "Decompression is running" not in caplog.text
    # THEN should not output "Started decompression"
    assert "Started decompression" not in caplog.text
    # THEN should not output "Creating links"
    assert "Creating links" not in caplog.text
    # THEN mip should start
    assert "MIP rd-dna run started" in caplog.text

