""" Test the CLI for run mip-rna """

import logging

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from pytest_mock import MockFixture

from cg.apps.scout.scoutapi import ScoutAPI
from cg.cli.workflow.mip_rna.base import start, start_available
from cg.constants.process import EXIT_SUCCESS
from cg.meta.compress import CompressAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import CGConfig
from cg.store.crud.read import ReadHandler
from cg.store.models import Case


def setup_mocks(
    mocker,
    can_at_least_one_sample_be_decompressed: bool = False,
    get_case_to_analyze: Case = None,
    decompress_spring: bool = False,
    is_spring_decompression_needed: bool = False,
    is_spring_decompression_running: bool = False,
) -> None:
    """Helper function to set up the necessary mocks for the decompression logics."""
    mocker.patch.object(ReadHandler, "get_cases_to_analyze")
    ReadHandler.get_cases_to_analyze.return_value = [get_case_to_analyze]

    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_needed")
    PrepareFastqAPI.is_spring_decompression_needed.return_value = is_spring_decompression_needed

    mocker.patch.object(PrepareFastqAPI, "can_at_least_one_sample_be_decompressed")
    PrepareFastqAPI.can_at_least_one_sample_be_decompressed.return_value = (
        can_at_least_one_sample_be_decompressed
    )

    mocker.patch.object(CompressAPI, "decompress_spring")
    CompressAPI.decompress_spring.return_value = decompress_spring

    mocker.patch.object(PrepareFastqAPI, "is_spring_decompression_running")
    PrepareFastqAPI.is_spring_decompression_running.return_value = is_spring_decompression_running

    mocker.patch.object(PrepareFastqAPI, "add_decompressed_fastq_files_to_housekeeper")
    PrepareFastqAPI.add_decompressed_fastq_files_to_housekeeper.return_value = None

    mocker.patch.object(MipRNAAnalysisAPI, "get_panel_bed")
    MipRNAAnalysisAPI.get_panel_bed.return_value = "a_string"

    mocker.patch.object(
        ScoutAPI,
        "export_managed_variants",
        return_value=["a str"],
    )

    mocker.patch.object(ReadHandler, "are_all_illumina_runs_on_disk")
    ReadHandler.are_all_illumina_runs_on_disk.return_value = True


def test_spring_decompression_needed_and_started(
    caplog: LogCaptureFixture,
    case: Case,
    cli_runner: CliRunner,
    mip_rna_context: CGConfig,
    mocker: MockFixture,
):
    """Tests starting the MIP analysis when decompression is needed"""
    caplog.set_level(logging.INFO)

    # GIVEN a case is available for analysis
    # GIVEN all samples in the case has dna application type
    # GIVEN the latest analysis has not started
    # GIVEN spring decompression is needed
    # GIVEN there are spring files that can be decompressed
    # GIVEN there are flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=True,
        get_case_to_analyze=case,
        decompress_spring=True,
        is_spring_decompression_needed=True,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_rna_context)

    # THEN command should run without errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should be announced that spring decompression is started
    assert "Decompression started for" in caplog.text


def test_spring_decompression_needed_and_start_failed(
    caplog: LogCaptureFixture,
    case: Case,
    cli_runner: CliRunner,
    mip_rna_context: CGConfig,
    mocker: MockFixture,
):
    """Tests starting the MIP analysis when decompression is needed but fail to start"""
    caplog.set_level(logging.INFO)

    # GIVEN a case is available for analysis
    # GIVEN all samples in the case has dna application type
    # GIVEN the latest analysis has not started
    # GIVEN spring decompression is needed
    # GIVEN there are spring files that can be decompressed
    # GIVEN there are flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=True,
        get_case_to_analyze=case,
        decompress_spring=False,
        is_spring_decompression_needed=True,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_rna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert "Decompression failed to start for" in caplog.text


def test_spring_decompression_needed_and_cant_start(
    caplog: LogCaptureFixture,
    case: Case,
    cli_runner: CliRunner,
    mip_rna_context: CGConfig,
    mocker: MockFixture,
):
    """Tests starting the MIP analysis when decompression is needed but can't start"""
    caplog.set_level(logging.INFO)

    # GIVEN a case is available for analysis
    # GIVEN all samples in the case has dna application type
    # GIVEN the latest analysis has not started
    # GIVEN spring decompression is needed
    # GIVEN no spring files can be decompressed
    # GIVEN spring decompression is not running
    # GIVEN there are flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=False,
        get_case_to_analyze=case,
        decompress_spring=False,
        is_spring_decompression_needed=True,
        is_spring_decompression_running=False,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_rna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert "Decompression can not be started for" in caplog.text


def test_decompression_cant_start_and_is_running(
    mocker: MockFixture,
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    mip_rna_context: CGConfig,
    case: Case,
):
    """Tests starting the MIP analysis when decompression is needed but can't start"""
    caplog.set_level(logging.INFO)

    # GIVEN a case is available for analysis
    # GIVEN all samples in the case has dna application type
    # GIVEN the latest analysis has not started
    # GIVEN spring decompression is needed
    # GIVEN no spring files can be decompressed
    # GIVEN spring decompression is running
    # GIVEN there are flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=False,
        get_case_to_analyze=case,
        decompress_spring=False,
        is_spring_decompression_needed=True,
        is_spring_decompression_running=True,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_rna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert "Decompression is running for" in caplog.text


def test_case_needs_to_be_stored(
    mocker: MockFixture,
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    mip_rna_context: CGConfig,
    case: Case,
):
    """Test starting MIP when files are decompressed but not stored in housekeeper"""
    caplog.set_level(logging.INFO)

    # GIVEN a case is available for analysis
    # GIVEN all samples in the case has dna application type
    # GIVEN the latest analysis has not started
    # GIVEN spring decompression is not needed
    # GIVEN fastqs linked in housekeeper are checked successfully
    # GIVEN spring decompression is not running
    # GIVEN a panel file is created
    # GIVEN there are flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=False,
        get_case_to_analyze=case,
        decompress_spring=False,
        is_spring_decompression_needed=False,
        is_spring_decompression_running=False,
        mocker=mocker,
    )

    # GIVEN that, a panel is returned
    mocker.patch.object(
        mip_rna_context.scout_api_37,
        "export_panels",
        return_value=["OMIM-AUTO"],
    )
    # WHEN MIP analysis is started
    result = cli_runner.invoke(start, [case.internal_id, "--dry-run"], obj=mip_rna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN the add_decompressed_fastq_files_to_housekeeper method should have been called
    assert PrepareFastqAPI.add_decompressed_fastq_files_to_housekeeper.call_count
