""" Test the CLI for run mip-dna """

import logging

from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from cg.cli.workflow.mip_dna.base import start, start_available
from cg.constants.process import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from click.testing import CliRunner

from cg.store.models import Family
from tests.cli.workflow.mip.conftest import setup_mocks


def test_spring_decompression_needed_and_started(
    caplog: LogCaptureFixture,
    case_obj: Family,
    cli_runner: CliRunner,
    mip_dna_context: CGConfig,
    mocker: MockFixture,
):
    """Tests starting the MIP analysis when decompression is needed"""
    caplog.set_level(logging.INFO)

    # GIVEN a case is available for analysis
    # GIVEN all samples in the case has dna application type
    # GIVEN the latest analysis has not started
    # GIVEN spring decompression is needed
    # GIVEN there is spring files that can be decompressed
    # GIVEN there is spring files that can be decompressed
    # GIVEN there is flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=True,
        case_to_analyze=case_obj,
        decompress_spring=True,
        has_latest_analysis_started=False,
        is_dna_only_case=True,
        is_spring_decompression_needed=True,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should be announced that spring decompression is started
    # assert "Decompression started for" in caplog.text
    assert "Decompression started for" in caplog.text


def test_spring_decompression_needed_and_start_failed(
    caplog: LogCaptureFixture,
    case_obj: Family,
    cli_runner: CliRunner,
    mip_dna_context: CGConfig,
    mocker: MockFixture,
):
    """Tests starting the MIP analysis when decompression is needed but fail to start"""
    caplog.set_level(logging.INFO)

    # GIVEN a case is available for analysis
    # GIVEN all samples in the case has dna application type
    # GIVEN the latest analysis has not started
    # GIVEN spring decompression is needed
    # GIVEN there is spring files that can be decompressed
    # GIVEN there is flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=True,
        case_to_analyze=case_obj,
        decompress_spring=False,
        has_latest_analysis_started=False,
        is_dna_only_case=True,
        is_spring_decompression_needed=True,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert f"Decompression failed to start for" in caplog.text


def test_spring_decompression_needed_and_cant_start(
    caplog: LogCaptureFixture,
    case_obj: Family,
    cli_runner: CliRunner,
    mip_dna_context: CGConfig,
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
    # GIVEN there is flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=False,
        case_to_analyze=case_obj,
        decompress_spring=False,
        has_latest_analysis_started=False,
        is_dna_only_case=True,
        is_spring_decompression_needed=True,
        is_spring_decompression_running=False,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert f"Decompression can not be started for" in caplog.text


def test_decompression_cant_start_and_is_running(
    mocker: MockFixture,
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    mip_dna_context: CGConfig,
    case_obj: Family,
):
    """Tests starting the MIP analysis when decompression is needed but can't start"""
    caplog.set_level(logging.INFO)

    # GIVEN a case is available for analysis
    # GIVEN all samples in the case has dna application type
    # GIVEN the latest analysis has not started
    # GIVEN spring decompression is needed
    # GIVEN no spring files can be decompressed
    # GIVEN spring decompression is running
    # GIVEN there is flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=False,
        case_to_analyze=case_obj,
        decompress_spring=False,
        has_latest_analysis_started=False,
        is_dna_only_case=True,
        is_spring_decompression_needed=True,
        is_spring_decompression_running=True,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert f"Decompression is running for" in caplog.text


def test_case_needs_to_be_stored(
    mocker: MockFixture,
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    mip_dna_context: CGConfig,
    case_obj: Family,
):
    """Test starting MIP when files are decompressed but not stored in housekeeper"""
    caplog.set_level(logging.INFO)

    # GIVEN a case is available for analysis
    # GIVEN all samples in the case has dna application type
    # GIVEN the latest analysis has not starte
    # GIVEN spring decompression is not needed
    # GIVEN fastqs linked in housekeeper are checked successfully
    # GIVEN spring decompression is not running
    # GIVEN a panel file is created
    # GIVEN there is flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=False,
        case_to_analyze=case_obj,
        decompress_spring=False,
        has_latest_analysis_started=False,
        is_dna_only_case=True,
        is_spring_decompression_needed=False,
        is_spring_decompression_running=False,
        mocker=mocker,
    )

    # WHEN MIP analysis is started
    result = cli_runner.invoke(start, [case_obj.internal_id, "--dry-run"], obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN fastq files should be added to housekeeper
    assert "Linking fastq files in housekeeper for case" in caplog.text
