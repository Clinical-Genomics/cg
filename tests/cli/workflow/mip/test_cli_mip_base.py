""" Test the CLI for run mip-dna """

import logging

from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.mip_dna.base import start, start_available
from cg.meta.compress import CompressAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.store.api.status import StatusHandler


def test_spring_decompression_needed_and_started(
    mocker, cli_runner, caplog, dna_mip_context, case_id
):
    """Tests starting the MIP analysis when decompression is needed"""
    caplog.set_level(logging.INFO)

    # GIVEN a case to analyze
    mip_api = dna_mip_context.meta_apis["analysis_api"]
    case_object = mip_api.status_db.family(case_id)

    # GIVEN a case is available for analysis
    mocker.patch.object(StatusHandler, "cases_to_analyze")
    StatusHandler.cases_to_analyze.return_value = [case_object]

    # GIVEN all samples in the case has dna application type
    mocker.patch.object(MipAnalysisAPI, "is_dna_only_case")
    MipAnalysisAPI.is_dna_only_case.return_value = True

    # GIVEN the latest analysis has not started
    mocker.patch.object(TrailblazerAPI, "has_latest_analysis_started")
    TrailblazerAPI.has_latest_analysis_started.return_value = False

    # GIVEN spring decompression is needed
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = True

    # GIVEN there is spring files that can be decompressed
    mocker.patch.object(PrepareFastqAPI, "can_at_least_one_sample_be_decompressed")
    PrepareFastqAPI.can_at_least_one_sample_be_decompressed.return_value = True

    # GIVEN there is spring files that can be decompressed
    mocker.patch.object(CompressAPI, "decompress_spring")
    CompressAPI.decompress_spring.return_value = True

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=dna_mip_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is started
    # assert "Decompression started for" in caplog.text
    assert "Decompression started for" in caplog.text


def test_spring_decompression_needed_and_start_failed(
    mocker,
    cli_runner,
    caplog,
    dna_mip_context,
    case_id,
):
    """Tests starting the MIP analysis when decompression is needed but fail to start"""
    caplog.set_level(logging.INFO)

    # GIVEN a case to analyze
    mip_api = dna_mip_context.meta_apis["analysis_api"]
    case_object = mip_api.status_db.family(case_id)

    # GIVEN a case is available for analysis
    mocker.patch.object(StatusHandler, "cases_to_analyze")
    StatusHandler.cases_to_analyze.return_value = [case_object]

    # GIVEN all samples in the case has dna application type
    mocker.patch.object(MipAnalysisAPI, "is_dna_only_case")
    MipAnalysisAPI.is_dna_only_case.return_value = True

    # GIVEN the latest analysis has not started
    mocker.patch.object(TrailblazerAPI, "has_latest_analysis_started")
    TrailblazerAPI.has_latest_analysis_started.return_value = False

    # GIVEN spring decompression is needed
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = True

    # GIVEN there is spring files that can be decompressed
    mocker.patch.object(PrepareFastqAPI, "can_at_least_one_sample_be_decompressed")
    PrepareFastqAPI.can_at_least_one_sample_be_decompressed.return_value = True

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=dna_mip_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert f"Decompression failed to start for" in caplog.text


def test_spring_decompression_needed_and_cant_start(
    mocker, cli_runner, caplog, dna_mip_context, case_id
):
    """Tests starting the MIP analysis when decompression is needed but can't start"""
    caplog.set_level(logging.INFO)

    # GIVEN a case to analyze
    mip_api = dna_mip_context.meta_apis["analysis_api"]
    case_object = mip_api.status_db.family(case_id)

    # GIVEN a case is available for analysis
    mocker.patch.object(StatusHandler, "cases_to_analyze")
    StatusHandler.cases_to_analyze.return_value = [case_object]

    # GIVEN all samples in the case has dna application type
    mocker.patch.object(MipAnalysisAPI, "is_dna_only_case")
    MipAnalysisAPI.is_dna_only_case.return_value = True

    # GIVEN the latest analysis has not started
    mocker.patch.object(TrailblazerAPI, "has_latest_analysis_started")
    TrailblazerAPI.has_latest_analysis_started.return_value = False

    # GIVEN spring decompression is needed
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = True

    # GIVEN no spring files can be decompressed
    mocker.patch.object(PrepareFastqAPI, "can_at_least_one_sample_be_decompressed")
    PrepareFastqAPI.can_at_least_one_sample_be_decompressed.return_value = False

    # GIVEN spring decompression is not running
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_running")
    PrepareFastqAPI.is_spring_decompression_running.return_value = False

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=dna_mip_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert f"Decompression can not be started for" in caplog.text


def test_decompression_cant_start_and_is_running(
    mocker, cli_runner, caplog, dna_mip_context, case_id
):
    """Tests starting the MIP analysis when decompression is needed but can't start"""
    caplog.set_level(logging.INFO)

    # GIVEN a case to analyze
    mip_api = dna_mip_context.meta_apis["analysis_api"]
    case_object = mip_api.status_db.family(case_id)

    # GIVEN a case is available for analysis
    mocker.patch.object(StatusHandler, "cases_to_analyze")
    StatusHandler.cases_to_analyze.return_value = [case_object]

    # GIVEN all samples in the case has dna application type
    mocker.patch.object(MipAnalysisAPI, "is_dna_only_case")
    MipAnalysisAPI.is_dna_only_case.return_value = True

    # GIVEN the latest analysis has not started
    mocker.patch.object(TrailblazerAPI, "has_latest_analysis_started")
    TrailblazerAPI.has_latest_analysis_started.return_value = False

    # GIVEN spring decompression is needed
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = True

    # GIVEN no spring files can be decompressed
    mocker.patch.object(PrepareFastqAPI, "can_at_least_one_sample_be_decompressed")
    PrepareFastqAPI.can_at_least_one_sample_be_decompressed.return_value = False

    # GIVEN spring decompression is running
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_running")
    PrepareFastqAPI.is_spring_decompression_running.return_value = True

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=dna_mip_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert f"Decompression is running for" in caplog.text


def test_case_needs_to_be_stored(mocker, cli_runner, caplog, case_id, dna_mip_context):
    """Test starting MIP when files are decompressed but not stored in housekeeper"""
    caplog.set_level(logging.INFO)

    # GIVEN a case to analyze
    mip_api = dna_mip_context.meta_apis["analysis_api"]
    case_object = mip_api.status_db.family(case_id)

    # GIVEN a case is available for analysis
    mocker.patch.object(StatusHandler, "cases_to_analyze")
    StatusHandler.cases_to_analyze.return_value = [case_object]

    # GIVEN all samples in the case has dna application type
    mocker.patch.object(MipDNAAnalysisAPI, "is_dna_only_case")
    MipDNAAnalysisAPI.is_dna_only_case.return_value = True

    # GIVEN the latest analysis has not started
    mocker.patch.object(TrailblazerAPI, "has_latest_analysis_started")
    TrailblazerAPI.has_latest_analysis_started.return_value = False

    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing")
    TrailblazerAPI.is_latest_analysis_ongoing.return_value = False

    # GIVEN spring decompression is not needed
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = False

    # GIVEN fastqs linked in housekeeper are checked successfully
    mocker.patch.object(PrepareFastqAPI, "check_fastq_links")
    PrepareFastqAPI.check_fastq_links.return_value = None

    # GIVEN spring decompression is not running
    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_running")
    PrepareFastqAPI.is_spring_decompression_running.return_value = False

    # GIVEN a panel file is created
    mocker.patch.object(MipDNAAnalysisAPI, "panel")
    MipDNAAnalysisAPI.panel.return_value = "bla"

    # WHEN MIP analysis is started
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=dna_mip_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN fastq files should be added to housekeeper
    assert "Linking fastq files in housekeeper for case" in caplog.text
