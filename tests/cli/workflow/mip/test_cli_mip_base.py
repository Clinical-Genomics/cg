""" Test the CLI for run mip-dna """

import logging

import mock
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from pytest_mock import MockFixture

from cg.cli.workflow.mip_dna.base import start, start_available
from cg.constants.process import EXIT_SUCCESS
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from tests.cli.workflow.mip.conftest import setup_mocks
from tests.store.conftest import case_obj


def test_spring_decompression_needed_and_started(
    caplog: LogCaptureFixture,
    case: Case,
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
    # GIVEN there are spring files that can be decompressed
    # GIVEN there are flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=True,
        case_to_analyze=case,
        decompress_spring=True,
        has_latest_analysis_started=False,
        is_spring_decompression_needed=True,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should be announced that spring decompression is started
    assert "Decompression started for" in caplog.text


def test_spring_decompression_needed_and_start_failed(
    caplog: LogCaptureFixture,
    case: Case,
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
    # GIVEN there are spring files that can be decompressed
    # GIVEN there are flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=True,
        case_to_analyze=case,
        decompress_spring=False,
        has_latest_analysis_started=False,
        is_spring_decompression_needed=True,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert "Decompression failed to start for" in caplog.text


def test_spring_decompression_needed_and_cant_start(
    caplog: LogCaptureFixture,
    case: Case,
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
    # GIVEN there are flow cells for the case
    setup_mocks(
        can_at_least_one_sample_be_decompressed=False,
        case_to_analyze=case,
        decompress_spring=False,
        has_latest_analysis_started=False,
        is_spring_decompression_needed=True,
        is_spring_decompression_running=False,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert "Decompression can not be started for" in caplog.text


def test_decompression_cant_start_and_is_running(
    mocker: MockFixture,
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    mip_dna_context: CGConfig,
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
        case_to_analyze=case,
        decompress_spring=False,
        has_latest_analysis_started=False,
        is_spring_decompression_needed=True,
        is_spring_decompression_running=True,
        mocker=mocker,
    )

    # WHEN an MIP analysis is started
    result = cli_runner.invoke(start_available, obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN it should be announced that spring decompression is needed but fail to start
    assert "Decompression is running for" in caplog.text


def test_case_needs_to_be_stored(
    mocker: MockFixture,
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    mip_dna_context: CGConfig,
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
        case_to_analyze=case,
        decompress_spring=False,
        has_latest_analysis_started=False,
        is_spring_decompression_needed=False,
        is_spring_decompression_running=False,
        mocker=mocker,
    )

    # GIVEN that, a panel is returned
    with mock.patch.object(
        mip_dna_context.scout_api,
        "export_panels",
        return_value=["OMIM-AUTO"],
    ):
        # WHEN MIP analysis is started
        result = cli_runner.invoke(start, [case.internal_id, "--dry-run"], obj=mip_dna_context)

    # THEN command should run without errors
    assert result.exit_code == 0

    # THEN the add_decompressed_fastq_files_to_housekeeper method should have been called
    assert PrepareFastqAPI.add_decompressed_fastq_files_to_housekeeper.call_count
