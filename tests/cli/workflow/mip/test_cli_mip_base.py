""" Test the CLI for run mip-dna """

import logging

from cg.meta.workflow.mip import MipAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.cli.workflow.mip_dna.base import start, start_available
from cg.store.api.status import StatusHandler

from tests.meta.conftest import fixture_analysis_api
from tests.meta.conftest import fixture_mip_hk_store


def test_spring_decompression_needed_and_started(
    mocker, cli_runner, caplog, dna_mip_context, case_id, analysis_api
):
    caplog.set_level(logging.INFO)

    mip_api = analysis_api
    case_object = mip_api.get_case_object(case_id)

    mocker.patch.object(StatusHandler, "cases_to_analyze")
    StatusHandler.cases_to_analyze.return_value = [case_object]

    mocker.patch.object(MipAnalysisAPI, "is_dna_only_case")
    MipAnalysisAPI.is_dna_only_case.return_value = True

    case_object.internal_id = "ADM1"

    mocker.patch.object(MipAnalysisAPI, "has_latest_analysis_started")
    MipAnalysisAPI.has_latest_analysis_started.return_value = False

    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = True

    mocker.patch.object(PrepareFastqAPI, "start_spring_decompression")
    PrepareFastqAPI.start_spring_decompression.return_value = True

    result = cli_runner.invoke(start_available, obj=dna_mip_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    assert "started decompression instead" in caplog.text


def test_spring_decompression_needed_and_start_failed(
    mocker, cli_runner, caplog, dna_mip_context, case_id, analysis_api
):
    caplog.set_level(logging.INFO)

    mip_api = analysis_api
    case_object = mip_api.get_case_object(case_id)

    mocker.patch.object(StatusHandler, "cases_to_analyze")
    StatusHandler.cases_to_analyze.return_value = [case_object]

    mocker.patch.object(MipAnalysisAPI, "is_dna_only_case")
    MipAnalysisAPI.is_dna_only_case.return_value = True

    case_object.internal_id = "ADM1"

    mocker.patch.object(MipAnalysisAPI, "has_latest_analysis_started")
    MipAnalysisAPI.has_latest_analysis_started.return_value = False

    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = True

    mocker.patch.object(PrepareFastqAPI, "start_spring_decompression")
    PrepareFastqAPI.start_spring_decompression.return_value = False

    result = cli_runner.invoke(start_available, obj=dna_mip_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    assert "Neither the analysis, nor the decompression needed" in caplog.text


def test_case_needs_to_be_stored(
    mocker, cli_runner, caplog, case_id, analysis_api, dna_mip_context
):
    caplog.set_level(logging.INFO)

    mip_api = analysis_api
    case_object = mip_api.get_case_object(case_id)

    mocker.patch.object(StatusHandler, "cases_to_analyze")
    StatusHandler.cases_to_analyze.return_value = [case_object]

    mocker.patch.object(MipAnalysisAPI, "is_dna_only_case")
    MipAnalysisAPI.is_dna_only_case.return_value = True

    case_object.internal_id = "ADM1"

    mocker.patch.object(MipAnalysisAPI, "has_latest_analysis_started")
    MipAnalysisAPI.has_latest_analysis_started.return_value = False

    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = False

    mocker.patch.object(PrepareFastqAPI, "check_fastq_links")
    PrepareFastqAPI.check_fastq_links.return_value = None

    mocker.patch.object(MipAnalysisAPI, "panel")
    MipAnalysisAPI.panel.return_value = "bla"

    result = cli_runner.invoke(
        start, ["ADM1", "--panel-bed", "panel.bed", "--dry-run"], obj=dna_mip_context
    )

    # THEN command should run without errors
    assert result.exit_code == 0

    assert "Linking fastq files in housekeeper for case" in caplog.text
