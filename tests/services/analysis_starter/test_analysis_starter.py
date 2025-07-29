from pathlib import Path
from subprocess import CalledProcessError
from typing import cast
from unittest.mock import create_autospec

import pytest
import requests
from pytest_mock import MockerFixture
from requests import Response

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Workflow
from cg.constants.priority import Priority, SlurmQos
from cg.exc import AnalysisNotReadyError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.abstract import (
    ParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import creator
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.services.analysis_starter.service import AnalysisStarter
from cg.services.analysis_starter.submitters.seqera_platform.submitter import (
    SeqeraPlatformSubmitter,
)
from cg.services.analysis_starter.tracker.implementations.nextflow import NextflowTracker
from cg.store.models import Case, Sample
from cg.store.store import Store


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.MICROSALT,
        Workflow.RNAFUSION,
        Workflow.RAREDISEASE,
        Workflow.TAXPROFILER,
    ],
)
@pytest.mark.parametrize(
    "attribute_name, function_name, error, expected_exit",
    [
        ("tracker", "ensure_analysis_not_ongoing", None, True),
        ("input_fetcher", "ensure_files_are_ready", AnalysisNotReadyError, True),
        ("tracker", "ensure_analysis_not_ongoing", Exception, False),
    ],
    ids=["Success", "Fastqs missing", "General error"],
)
def test_analysis_starter_start_available_error_handling(
    workflow: Workflow,
    cg_context: CGConfig,
    attribute_name: str,
    function_name: str,
    error: type[Exception],
    expected_exit: bool,
):
    """Test that the AnalysisStarter returns correct exit values depending on the errors raised."""
    # GIVEN a Store with a mock case
    mock_store = create_autospec(Store)
    mock_case = create_autospec(Case)
    mock_store.get_cases_to_analyze.return_value = [mock_case]

    # GIVEN an analysis starter
    analysis_starter = AnalysisStarter(
        configurator=create_autospec(NextflowConfigurator),
        input_fetcher=create_autospec(FastqFetcher),
        store=mock_store,
        submitter=create_autospec(SeqeraPlatformSubmitter),
        tracker=create_autospec(NextflowTracker),
        workflow=workflow,
    )

    # GIVEN that the AnalysisStarter mock raises an error as specified in the parametrisation
    mocked_attribute = getattr(analysis_starter, attribute_name)
    mocked_function = getattr(mocked_attribute, function_name)
    mocked_function.side_effect = error

    # WHEN starting all available cases
    succeeded: bool = analysis_starter.start_available()

    # THEN it should have exited with the expected value
    assert succeeded == expected_exit


# TODO: Use this test as inspiration for an integration test for the start mudule
def test_rnafusion_start(
    cg_context: CGConfig,
    http_workflow_launch_response: Response,
    mocker: MockerFixture,
):
    # GIVEN a case_id
    case_id: str = "case_id"

    # GIVEN an analysis starter factory
    analysis_starter_factory = AnalysisStarterFactory(cg_context)

    # GIVEN a store that all our components use a mocked store
    mock_store = create_autospec(Store)
    analysis_starter_factory.store = mock_store
    analysis_starter_factory.configurator_factory.store = mock_store
    analysis_starter = analysis_starter_factory.get_analysis_starter_for_workflow(
        Workflow.RNAFUSION
    )

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
    mocker.patch.object(
        RNAFusionSampleSheetCreator, "_get_sample_sheet_content_per_sample", return_value=[[""]]
    )

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
    analysis_starter.start(case_id)

    # THEN all the necessary files should have been written
    configurator: NextflowConfigurator = cast(NextflowConfigurator, analysis_starter.configurator)
    config_file_creator: NextflowConfigFileCreator = configurator.config_file_creator
    sample_sheet_creator: NextflowSampleSheetCreator = configurator.sample_sheet_creator
    params_file_creator: ParamsFileCreator = configurator.params_file_creator
    case_path = configurator._get_case_path(case_id)
    assert config_file_creator.get_file_path(case_id=case_id, case_path=case_path).exists()
    assert sample_sheet_creator.get_file_path(case_id=case_id, case_path=case_path).exists()
    assert params_file_creator.get_file_path(case_id=case_id, case_path=case_path).exists()

    # THEN the case should have been submitted and tracked
    submit_mock.assert_called_once()
    track_mock.assert_called_once()


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.RNAFUSION,
        Workflow.RAREDISEASE,
        Workflow.TAXPROFILER,
    ],
)
def test_nextflow_start(workflow: Workflow):
    """Test that Nextflow cases can be started successfully."""
    # GIVEN a Taxprofiler case_id
    case_id: str = "case_id"

    # GIVEN a set of flags
    flags: dict[str, str] = {"flag1": "value1", "flag2": "value2"}

    # GIVEN a Taxprofiler configurator that returns a mock case config
    configurator: NextflowConfigurator = create_autospec(NextflowConfigurator)
    mock_case_config: NextflowCaseConfig = create_autospec(NextflowCaseConfig)
    configurator.configure.return_value = mock_case_config

    # GIVEN a FastqFetcher
    input_fetcher: FastqFetcher = create_autospec(FastqFetcher)

    # GIVEN a Store
    mock_store: Store = create_autospec(Store)

    # GIVEN a SeqeraPlatformSubmitter
    submitter: SeqeraPlatformSubmitter = create_autospec(SeqeraPlatformSubmitter)
    mock_tower_id: str = "tower_id"
    submitter.submit.return_value = mock_tower_id

    # GIVEN a NextflowTracker
    tracker: NextflowTracker = create_autospec(NextflowTracker)

    # GIVEN an analysis starter
    analysis_starter = AnalysisStarter(
        configurator=configurator,
        input_fetcher=input_fetcher,
        store=mock_store,
        submitter=submitter,
        tracker=tracker,
        workflow=workflow,
    )

    # WHEN starting the Taxprofiler case
    analysis_starter.start(case_id, **flags)

    # THEN the analysis should be started successfully
    tracker.ensure_analysis_not_ongoing.assert_called_once_with(case_id)
    input_fetcher.ensure_files_are_ready.assert_called_once_with(case_id)
    configurator.configure.assert_called_once_with(case_id=case_id, **flags)
    tracker.set_case_as_running.assert_called_once_with(case_id)
    submitter.submit.assert_called_once_with(mock_case_config)
    tracker.track.assert_called_once_with(
        case_config=mock_case_config, tower_workflow_id=mock_tower_id
    )


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.RNAFUSION,
        Workflow.RAREDISEASE,
        Workflow.TAXPROFILER,
    ],
)
def test_nextflow_start_error_raised_in_run_and_track(workflow: Workflow):
    """Test that an error raised in submitting the analysis job is handled correctly."""
    # GIVEN a case_id
    case_id: str = "case_id"

    # GIVEN an analysis starter
    analysis_starter = AnalysisStarter(
        configurator=create_autospec(NextflowConfigurator),
        input_fetcher=create_autospec(FastqFetcher),
        store=create_autospec(Store),
        submitter=create_autospec(SeqeraPlatformSubmitter),
        tracker=create_autospec(NextflowTracker),
        workflow=workflow,
    )

    # GIVEN that the submitter raises an error when submitting the analysis job
    expected_error = CalledProcessError(returncode=1, cmd="submit_command")
    analysis_starter.submitter.submit.side_effect = expected_error

    # WHEN the case is started
    with pytest.raises(CalledProcessError):
        analysis_starter.start(case_id)

    # THEN the error is propagated and the case should be set as not running
    analysis_starter.tracker.set_case_as_not_running.assert_called_once_with(case_id)
