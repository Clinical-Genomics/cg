"""Test the CLI for run mip-rna"""

import logging

from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.mip_rna.base import run
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI


def test_mip_rna_dry_run(cli_runner, caplog, case_id, email_address, mip_rna_context, mocker):
    caplog.set_level(logging.INFO)
    # GIVEN a cli function
    # WHEN we run a case in dry run mode

    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing", return_value=False)

    result = cli_runner.invoke(
        run, ["--dry-run", "--email", email_address, case_id], obj=mip_rna_context
    )

    # THEN the command should be printed
    assert result.exit_code == 0

    # THEN log should be printed
    assert "Running in dry-run mode" in caplog.text


def test_mip_rna_pipeline_dry_run(
    cli_runner, mocker, caplog, case_id, email_address, mip_rna_context
):
    caplog.set_level(logging.INFO)

    mocker.patch.object(MipRNAAnalysisAPI, "get_target_bed_from_lims", return_value="target_bed")
    mocker.patch.object(MipRNAAnalysisAPI, "run_analysis", return_value=0)

    # GIVEN a cli function
    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(
        run, ["--mip-dry-run", "--email", email_address, case_id], obj=mip_rna_context
    )

    # THEN command is run successfully
    assert result.exit_code == 0

    # THEN log should be printed
    assert "Executed MIP in dry-run mode" in caplog.text


def test_mip_rna_run_successfully(
    cli_runner,
    mocker,
    caplog,
    case_id,
    email_address,
    mip_rna_context,
    case_qc_sample_info_path,
):
    caplog.set_level(logging.INFO)

    mocker.patch.object(MipRNAAnalysisAPI, "get_target_bed_from_lims", return_value="target_bed")
    mocker.patch.object(MipRNAAnalysisAPI, "run_analysis", return_value=0)
    mocker.patch.object(MipRNAAnalysisAPI, "on_analysis_started")

    # GIVEN that the case has a QC sample info file
    mocker.patch.object(
        MipRNAAnalysisAPI, "get_sample_info_path", return_value=case_qc_sample_info_path
    )

    # GIVEN a cli function
    # WHEN we run a case
    result = cli_runner.invoke(run, ["--email", email_address, case_id], obj=mip_rna_context)

    # THEN command is run successfully
    assert result.exit_code == 0

    # THEN log should be printed
    assert "mip-rna run started" in caplog.text


def test_mip_rna_run_fail(
    cli_runner,
    mocker,
    caplog,
    case_id,
    email_address,
    mip_rna_context,
    tb_api,
):
    """Test already ongoing analysis MIP RNA run"""

    caplog.set_level(logging.INFO)

    mocker.patch.object(MipRNAAnalysisAPI, "get_target_bed_from_lims", return_value="target_bed")
    mocker.patch.object(MipRNAAnalysisAPI, "run_analysis", return_value=0)

    mocker.patch.object(tb_api, "is_latest_analysis_ongoing")
    tb_api.is_latest_analysis_ongoing.return_value = True

    # GIVEN a cli function
    # WHEN we run a case
    result = cli_runner.invoke(run, ["--email", email_address, case_id], obj=mip_rna_context)

    # THEN command should return an exit fail code
    assert result.exit_code == 1

    # THEN an error should be logged
    assert "Analysis still ongoing in Trailblazer" in caplog.text
