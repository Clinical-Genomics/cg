""" Test the CLI for run mip-dna """

import logging

from cg.cli.workflow.mip_dna.base import run
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI


def test_cg_dry_run(
    cli_runner, mocker, caplog, case_id, email_address, mip_dna_context, mip_dna_config_path
):
    """Test print the MIP run to console"""

    caplog.set_level(logging.INFO)

    mocker.patch.object(MipDNAAnalysisAPI, "get_target_bed_from_lims")
    MipDNAAnalysisAPI.get_target_bed_from_lims.return_value = mip_dna_config_path

    # GIVEN a cli function
    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(
        run, ["--dry-run", "--email", email_address, case_id], obj=mip_dna_context
    )
    # THEN command is run successfully
    assert result.exit_code == 0

    # THEN log should be printed
    assert "Running in dry-run mode" in caplog.text


def test_mip_dry_run(
    cli_runner, mocker, caplog, case_id, email_address, mip_dna_context, mip_dna_config_path
):
    """Test print the MIP run to console"""

    caplog.set_level(logging.INFO)

    mocker.patch.object(MipDNAAnalysisAPI, "get_target_bed_from_lims")
    MipDNAAnalysisAPI.get_target_bed_from_lims.return_value = mip_dna_config_path
    mocker.patch.object(MipDNAAnalysisAPI, "run_analysis")
    MipDNAAnalysisAPI.run_analysis.return_value = 0

    # GIVEN a cli function
    # WHEN we run a case in dry run mode
    result = cli_runner.invoke(
        run, ["--mip-dry-run", "--email", email_address, case_id], obj=mip_dna_context
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
    mip_dna_context,
    trailblazer_api,
    mip_dna_config_path,
    case_qc_sample_info_path,
):
    """Test print the MIP run"""

    caplog.set_level(logging.INFO)

    mocker.patch.object(MipDNAAnalysisAPI, "get_target_bed_from_lims")
    MipDNAAnalysisAPI.get_target_bed_from_lims.return_value = mip_dna_config_path
    mocker.patch.object(MipDNAAnalysisAPI, "run_analysis")
    MipDNAAnalysisAPI.run_analysis.return_value = 0

    mocker.patch.object(MipDNAAnalysisAPI, "on_analysis_started")

    # GIVEN that the case has a QC sample info file
    mocker.patch.object(MipDNAAnalysisAPI, "get_sample_info_path")
    MipDNAAnalysisAPI.get_sample_info_path.return_value = case_qc_sample_info_path

    # GIVEN a cli function
    # WHEN we run a case
    result = cli_runner.invoke(run, ["--email", email_address, case_id], obj=mip_dna_context)

    # THEN command is run successfully
    assert result.exit_code == 0

    # THEN log should be printed
    assert "mip-dna run started" in caplog.text


def test_mip_run_fail(
    cli_runner,
    mocker,
    caplog,
    case_id,
    email_address,
    mip_dna_context,
    tb_api,
    mip_dna_config_path,
):
    """Test already ongoing analysis MIP run"""

    caplog.set_level(logging.INFO)

    mocker.patch.object(MipDNAAnalysisAPI, "get_target_bed_from_lims")
    MipDNAAnalysisAPI.get_target_bed_from_lims.return_value = mip_dna_config_path
    mocker.patch.object(MipDNAAnalysisAPI, "run_analysis")
    MipDNAAnalysisAPI.run_analysis.return_value = 0

    mocker.patch.object(tb_api, "is_latest_analysis_ongoing")
    tb_api.is_latest_analysis_ongoing.return_value = True

    # GIVEN a cli function
    # WHEN we run a case
    result = cli_runner.invoke(run, ["--email", email_address, case_id], obj=mip_dna_context)

    # THEN command should return an exit fail code
    assert result.exit_code == 1

    # THEN an error should be logged
    assert "Analysis still ongoing in Trailblazer" in caplog.text
