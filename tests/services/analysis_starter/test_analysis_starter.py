from pathlib import Path
from unittest.mock import create_autospec

import pytest
import requests
from pytest_mock import MockerFixture

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Workflow
from cg.constants.priority import Priority, SlurmQos
from cg.exc import AnalysisNotReadyError, AnalysisRunningError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import creator
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.services.analysis_starter.service import AnalysisStarter
from cg.store.models import Case, Sample
from cg.store.store import Store


@pytest.mark.parametrize(
    "error, expected_exit",
    [
        (None, True),
        (AnalysisNotReadyError, True),
        (AnalysisRunningError, False),
        (Exception, False),
    ],
    ids=["Success", "Fastqs missing", "Analysis ongoing", "General error"],
)
def test_microsalt_analysis_starter_start_available_error_handling(
    cg_context: CGConfig, mocker: MockerFixture, error: type[Exception], expected_exit: bool
):
    # GIVEN an AnalysisStarter
    analysis_starter: AnalysisStarter = AnalysisStarterFactory(
        cg_context
    ).get_analysis_starter_for_workflow(Workflow.MICROSALT)

    # GIVEN that the start exits with a given behaviour
    mocker.patch.object(Store, "get_cases_to_analyze", return_value=[create_autospec(Case)])
    mocker.patch.object(AnalysisStarter, "start", return_value=None, side_effect=error)

    # WHEN starting all available cases
    succeeded: bool = analysis_starter.start_available()

    # THEN it should have exited with the expected value
    assert succeeded == expected_exit


def test_rnafusion_start(
    cg_context,
    http_workflow_launch_response,
    mocker: MockerFixture,
):
    analysis_starter: AnalysisStarter = AnalysisStarterFactory(
        cg_context
    ).get_analysis_starter_for_workflow(Workflow.RNAFUSION)

    # GIVEN a store that all our components use
    mock_store = create_autospec(Store)
    analysis_starter.store = mock_store
    analysis_starter.input_fetcher.status_db = mock_store
    configurator: NextflowConfigurator = analysis_starter.configurator
    configurator.store = mock_store
    configurator.sample_sheet_creator.store = mock_store
    configurator.config_file_creator.store = mock_store
    analysis_starter.tracker.store = mock_store

    # GIVEN a case with appropriate parameters set
    mock_case = create_autospec(Case)
    mock_sample = create_autospec(Sample)
    mock_store.get_case_by_internal_id.return_value = mock_case
    mock_case.samples = [mock_sample]
    mock_case.priority = Priority.standard
    mock_case.data_analysis = Workflow.RNAFUSION

    # GIVEN that the case is not downsampled nor external
    mock_store.is_case_down_sampled.return_value = False
    mock_store.is_case_external.return_value = False

    # GIVEN that the case has a priority and a workflow
    mock_store.get_case_priority.return_value = SlurmQos.NORMAL
    mock_store.get_case_workflow.return_value = Workflow.RNAFUSION

    # GIVEN that no analysis is running for the case
    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing", return_value=False)

    # GIVEN that the flow cells are on disk
    mock_store.are_all_illumina_runs_on_disk.return_value = True

    # GIVEN that there are no archived spring files
    mocker.patch.object(HousekeeperAPI, "get_archived_files_for_bundle", return_value=[])

    # GIVEN that no decompression is needed
    mocker.patch.object(FastqFetcher, "_resolve_decompression", return_value=None)

    # GIVEN that all fastq files are ready for analysis
    mocker.patch.object(FastqFetcher, "_are_fastq_files_ready_for_analysis", return_value=True)

    # GIVEN that the sample sheet content is created
    mocker.patch.object(RNAFusionSampleSheetCreator, "_get_sample_content", return_value=[[""]])

    # GIVEN that the files are written correctly
    mocker.patch.object(creator, "write_csv")

    # GIVEN that the fastq files exist
    mocker.patch.object(Path, "is_file", return_value=True)

    # GIVEN that the Fastq file headers are read correctly
    mocker.patch.object(
        creator,
        "read_gzip_first_line",
        side_effect=[
            "@ST-E00201:173:HCXXXXX:1:2106:22516:34834/1",
            "@ST-E00201:173:HCXXXXX:1:2106:22516:34834/2",
        ],
    )

    # GIVEN that the POST to the submitter is successful
    submit_mock = mocker.patch.object(
        requests,
        "post",
        return_value=http_workflow_launch_response,
    )

    # GIVEN that the Trailblazer tracking is successful
    tb_analysis = create_autospec(TrailblazerAnalysis)
    tb_analysis.id = 1
    track_mock = mocker.patch.object(
        TrailblazerAPI, "add_pending_analysis", return_value=tb_analysis
    )

    # WHEN starting a case
    analysis_starter.start("case_id")

    # THEN our mocks should have been called
    submit_mock.assert_called_once()
    track_mock.assert_called_once()
