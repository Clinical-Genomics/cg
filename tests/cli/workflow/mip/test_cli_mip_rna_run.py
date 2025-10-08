""" Test the CLI for run mip-rna """

import logging

from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.mip_rna.base import run
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI


def test_cg_dry_run(cli_runner, caplog, case_id, email_address, mip_rna_context, mocker):
    """Test print the MIP command to console"""

    caplog.set_level(logging.INFO)
    # GIVEN a cli function
    # WHEN we run a case in dry run mode

    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing")
    TrailblazerAPI.is_latest_analysis_ongoing.return_value = False

    result = cli_runner.invoke(
        run, ["--dry-run", "--email", email_address, case_id], obj=mip_rna_context
    )

    # THEN the command should be printed
    assert result.exit_code == 0

    # THEN log should be printed
    assert "Running in dry-run mode" in caplog.text


def test_mip_dry_run(cli_runner, mocker, caplog, case_id, email_address, mip_rna_context):
    """Test print the MIP run to console"""

    caplog.set_level(logging.INFO)

    mocker.patch.object(MipRNAAnalysisAPI, "get_target_bed_from_lims")
    MipRNAAnalysisAPI.get_target_bed_from_lims.return_value = "target_bed"
    mocker.patch.object(MipRNAAnalysisAPI, "run_analysis")
    MipRNAAnalysisAPI.run_analysis.return_value = 0

    # GIVEN a cli function
    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(
        run, ["--mip-dry-run", "--email", email_address, case_id], obj=mip_rna_context
    )

    # THEN command is run successfully
    assert result.exit_code == 0

    # THEN log should be printed
    assert "Executed MIP in dry-run mode" in caplog.text


def test_mip_run(
    cli_runner,
    mocker,
    caplog,
    case_id,
    email_address,
    mip_rna_context,
    trailblazer_api,
    mip_dna_config_path,
    case_qc_sample_info_path,
):
    """Test print the MIP run"""

    caplog.set_level(logging.INFO)

    mocker.patch.object(MipRNAAnalysisAPI, "get_target_bed_from_lims")
    MipRNAAnalysisAPI.get_target_bed_from_lims.return_value = "target_bed"
    mocker.patch.object(MipRNAAnalysisAPI, "run_analysis")
    MipRNAAnalysisAPI.run_analysis.return_value = 0

    mocker.patch.object(MipRNAAnalysisAPI, "on_analysis_started")

    # GIVEN that the case has a QC sample info file
    mocker.patch.object(MipRNAAnalysisAPI, "get_sample_info_path")
    MipRNAAnalysisAPI.get_sample_info_path.return_value = case_qc_sample_info_path

    # GIVEN a cli function
    # WHEN we run a case
    result = cli_runner.invoke(run, ["--email", email_address, case_id], obj=mip_rna_context)

    # THEN command is run successfully
    assert result.exit_code == 0

    # THEN log should be printed
    assert "mip-rna run started" in caplog.text
