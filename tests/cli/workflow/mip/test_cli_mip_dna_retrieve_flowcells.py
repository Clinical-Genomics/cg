""" Test the CLI for run mip-dna """
import logging
import os
from pathlib import Path

from cg.cli.workflow.mip_dna.base import retrieve_flowcells

CASE_ID = "yellowhog"
EMAIL = "james.holden@scilifelab.se"


def test_retrieve_flowcells_on_disk(cli_runner, mip_context, caplog, analysis_store_single_case):
    # GIVEN flowcells are on disk
    case_obj = analysis_store_single_case.family(internal_id=CASE_ID)
    assert case_obj
    assert case_obj.links
    for link in case_obj.links:
        sample = link.sample
        for flowcell in sample.flowcells:
            flowcell.status = "ondisk"

    # WHEN calling retrieve_flowcells
    caplog.set_level(logging.WARNING)
    result = cli_runner.invoke(retrieve_flowcells, ["-c", CASE_ID, "--dry-run"], obj=mip_context)

    # THEN no error should be thrown
    assert result.exit_code == 0
    # THEN should not output "not ready to run"
    assert "not ready to run" not in caplog.text

