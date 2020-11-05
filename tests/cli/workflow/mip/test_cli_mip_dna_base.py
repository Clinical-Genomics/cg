""" Test the CLI for run mip-dna """
import logging
import os
from pathlib import Path

from cg.cli.workflow.mip_dna.base import mip_dna

CASE_ID = "yellowhog"

def test_mip_dna(cli_runner, mip_context, caplog, hk_config_dict):
    # GIVEN fastqs are all decompressed and linked
    pedigree_path = mip_context.get("dna_api").get_pedigree_config_path(case_id="yellowhog")
    Path.mkdir(pedigree_path.parent, parents=True, exist_ok=True)
    os.link("tests/fixtures/apps/mip/dna/store/pedigree.yaml", pedigree_path)

    caplog.set_level(logging.INFO)
    # WHEN calling mip_dna
    result = cli_runner.invoke(mip_dna, ["-c", CASE_ID], obj=hk_config_dict, catch_exceptions=False)

    # THEN no error should be thrown
    print(result.output)
    assert result.exit_code == 0

    # THEN should not output "Decompression is running"
    # THEN should not output "Started decompression"
    # THEN should not output "Creating links"
    assert False

