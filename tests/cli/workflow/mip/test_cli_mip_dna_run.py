""" Test the CLI for run mip-dna """
import logging

from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.mip_dna.base import run
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI


def test_cg_dry_run(cli_runner, mocker, caplog, case_id, email_adress, dna_mip_context):
    """Test print the MIP run to console"""

    caplog.set_level(logging.INFO)

    mocker.patch.object(MipDNAAnalysisAPI, "get_target_bed_from_lims")
    MipDNAAnalysisAPI.get_target_bed_from_lims.return_value = (
        "tests/fixtures/apps/mip/rna/case_config.yaml"
    )
    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing")
    TrailblazerAPI.is_latest_analysis_ongoing.return_value = False

    # GIVEN a cli function
    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(
        run, ["--dry-run", "--email", email_adress, case_id], obj=dna_mip_context
    )
    # THEN command is run successfully
    assert result.exit_code == 0
