from pathlib import Path
from subprocess import CalledProcessError
from typing import cast
from unittest.mock import Mock, create_autospec

import pytest
import requests
from pytest_mock import MockerFixture
from requests import HTTPError, Response

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Workflow
from cg.constants.priority import Priority, SlurmQos
from cg.exc import AnalysisNotReadyError, SeqeraError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet import creator
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion_sample_sheet_creator import (
    RNAFusionSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.services.analysis_starter.configurator.models.microsalt import MicrosaltCaseConfig
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_submitter import (
    SeqeraPlatformSubmitter,
)
from cg.services.analysis_starter.submitters.submitter import Submitter
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.implementations.balsamic import BalsamicTracker
from cg.services.analysis_starter.tracker.implementations.microsalt import MicrosaltTracker
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.services.analysis_starter.tracker.implementations.nextflow_tracker import NextflowTracker
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def nextflow_case_config_with_session_id_and_workflow_id() -> NextflowCaseConfig:
    case_config: NextflowCaseConfig = create_autospec(NextflowCaseConfig)
    case_config.get_session_id = Mock(return_value="session_id")
    case_config.get_workflow_id = Mock(return_value="workflow_id")
    return case_config


@pytest.fixture
def analysis_starter_scenario(
    nextflow_case_config_with_session_id_and_workflow_id: NextflowCaseConfig,
) -> dict:
    """
    Return a dict with mocks for configurator, case_config, submitter, tracker and submit return
    value for testing the analysis starter for each pipeline.
    """
    return {
        Workflow.BALSAMIC: (
            create_autospec(BalsamicConfigurator),
            create_autospec(BalsamicCaseConfig),
            create_autospec(SubprocessSubmitter),
            create_autospec(BalsamicTracker),
            create_autospec(BalsamicCaseConfig),
        ),
        Workflow.MICROSALT: (
            create_autospec(MicrosaltConfigurator),
            create_autospec(MicrosaltCaseConfig),
            create_autospec(SubprocessSubmitter),
            create_autospec(MicrosaltTracker),
            create_autospec(MicrosaltCaseConfig),
        ),
        Workflow.MIP_DNA: (
            create_autospec(MIPDNAConfigurator),
            create_autospec(MIPDNACaseConfig),
            create_autospec(SubprocessSubmitter),
            create_autospec(MIPDNATracker),
            create_autospec(MIPDNACaseConfig),
        ),
        Workflow.RNAFUSION: (
            create_autospec(NextflowConfigurator),
            create_autospec(NextflowCaseConfig),
            create_autospec(SeqeraPlatformSubmitter),
            create_autospec(NextflowTracker),
            nextflow_case_config_with_session_id_and_workflow_id,
        ),
        Workflow.RAREDISEASE: (
            create_autospec(NextflowConfigurator),
            create_autospec(NextflowCaseConfig),
            create_autospec(SeqeraPlatformSubmitter),
            create_autospec(NextflowTracker),
            nextflow_case_config_with_session_id_and_workflow_id,
        ),
        Workflow.TAXPROFILER: (
            create_autospec(NextflowConfigurator),
            create_autospec(NextflowCaseConfig),
            create_autospec(SeqeraPlatformSubmitter),
            create_autospec(NextflowTracker),
            nextflow_case_config_with_session_id_and_workflow_id,
        ),
    }


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.BALSAMIC,
        Workflow.MICROSALT,
        Workflow.MIP_DNA,
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
    attribute_name: str,
    function_name: str,
    error: type[Exception],
    expected_exit: bool,
):
    """
    Test that the start_available command from AnalysisStarter returns correct exit values
    depending on the errors raised.
    """
    # GIVEN a Store with a mock case
    mock_store: TypedMock[Store] = create_typed_mock(Store)
    mock_case: Case = create_autospec(Case)
    mock_store.as_mock.get_cases_to_analyze.return_value = [mock_case]

    # GIVEN a Submitter
    submitter: Submitter = create_autospec(Submitter)
    submitter.submit = Mock(return_value=("session_id", "workflow_id"))

    # GIVEN an analysis starter
    analysis_starter = AnalysisStarter(
        configurator=create_autospec(NextflowConfigurator),
        input_fetcher=create_autospec(FastqFetcher),
        store=mock_store.as_type,
        submitter=submitter,
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


def test_rnafusion_start(
    cg_context: CGConfig,
    http_workflow_launch_response: Response,
    mocker: MockerFixture,
    http_get_workflow_response: Response,
):
    # GIVEN a case_id
    case_id: str = "case_id"

    # GIVEN an analysis starter factory
    analysis_starter_factory = AnalysisStarterFactory(cg_context)

    # GIVEN a store that all our components use a mocked store
    mock_store: Store = create_autospec(Store)
    analysis_starter_factory.store = mock_store
    analysis_starter_factory.configurator_factory.store = mock_store
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_workflow(
        Workflow.RNAFUSION
    )

    # GIVEN a case with appropriate parameters set
    mock_sample: Sample = create_autospec(Sample)
    mock_case: Case = create_autospec(Case, samples=[mock_sample])
    mock_store.get_case_by_internal_id_strict = Mock(return_value=mock_case)
    mock_case.priority = Priority.standard
    mock_case.data_analysis = Workflow.RNAFUSION

    # GIVEN that the case is not downsampled nor external
    mock_store.is_case_down_sampled = Mock(return_value=False)
    mock_store.is_case_external = Mock(return_value=False)

    # GIVEN that the case has a priority and a workflow
    mock_store.get_case_priority = Mock(return_value=SlurmQos.NORMAL)
    mock_store.get_case_workflow = Mock(return_value=Workflow.RNAFUSION)

    # GIVEN that no analysis is running for the case
    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing", return_value=False)

    # GIVEN that the flow cells are on disk
    mock_store.are_all_illumina_runs_on_disk = Mock(return_value=True)

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

    # GIVEN that the GET to the submitter is successful
    get_workflow_mock = mocker.patch.object(
        requests,
        "get",
        return_value=http_get_workflow_response,
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
    case_path = configurator._get_case_run_directory(case_id)
    assert Path(case_path, f"{case_id}_nextflow_config.json").exists()
    assert Path(case_path, f"{case_id}_samplesheet.csv").exists()
    assert Path(case_path, f"{case_id}_params_file.yaml").exists()

    # THEN the case should have been submitted and tracked
    submit_mock.assert_called_once()
    get_workflow_mock.assert_called_once()
    track_mock.assert_called_once()


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.BALSAMIC,
        Workflow.MICROSALT,
        Workflow.MIP_DNA,
        Workflow.RNAFUSION,
        Workflow.RAREDISEASE,
        Workflow.TAXPROFILER,
    ],
)
def test_start(
    workflow: Workflow,
    analysis_starter_scenario: dict,
):
    """Test that a case can be started successfully for all pipelines."""
    # GIVEN a case_id
    case_id: str = "case_id"

    # GIVEN a set of flags
    flags: dict[str, str] = {"flag1": "value1", "flag2": "value2"}

    # GIVEN a mock configurator, case config, submitter, tracker, and tower_id
    mock_configurator, mock_case_config, mock_submitter, mock_tracker, submit_result = (
        analysis_starter_scenario[workflow]
    )

    # GIVEN that the configure method from the configurator returns the mock case config
    mock_configurator.configure.return_value = mock_case_config

    # GIVEN a FastqFetcher
    input_fetcher: TypedMock[FastqFetcher] = create_typed_mock(FastqFetcher)

    # GIVEN a Store
    mock_store: Store = create_autospec(Store)

    # GIVEN that the submitter returns a (session id and tower id) or None when submitting the analysis
    mock_submitter.submit = Mock(return_value=submit_result)

    # GIVEN an analysis starter initialised with the previously mocked classes
    analysis_starter = AnalysisStarter(
        configurator=mock_configurator,
        input_fetcher=input_fetcher.as_type,
        store=mock_store,
        submitter=mock_submitter,
        tracker=mock_tracker,
        workflow=workflow,
    )

    # WHEN starting the case
    analysis_starter.start(case_id, **flags)

    # THEN the analysis should be started successfully
    mock_tracker.ensure_analysis_not_ongoing.assert_called_once_with(case_id)
    input_fetcher.as_mock.ensure_files_are_ready.assert_called_once_with(case_id)
    mock_configurator.configure.assert_called_once_with(case_id=case_id, **flags)
    mock_tracker.set_case_as_running.assert_called_once_with(case_id)
    mock_submitter.submit.assert_called_once_with(mock_case_config)
    mock_tracker.track.assert_called_once_with(case_config=submit_result)


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.BALSAMIC,
        Workflow.MICROSALT,
        Workflow.MIP_DNA,
    ],
)
def test_start_subprocess_error_raised_in_run_and_track(
    workflow: Workflow, analysis_starter_scenario: dict
):
    """Test that an error raised in submitting the analysis job is handled correctly."""
    # GIVEN a case_id
    case_id: str = "case_id"

    # GIVEN a mock configurator, submitter and tracker
    mock_configurator, _, mock_submitter, mock_tracker, _ = analysis_starter_scenario[workflow]

    # GIVEN that the submitter raises an error when submitting the analysis job
    expected_error = CalledProcessError(returncode=1, cmd="submit_command")
    mock_submitter.submit.side_effect = expected_error

    # GIVEN an analysis starter initialised with the previously mocked classes
    analysis_starter = AnalysisStarter(
        configurator=mock_configurator,
        input_fetcher=create_autospec(FastqFetcher),
        store=create_autospec(Store),
        submitter=mock_submitter,
        tracker=mock_tracker,
        workflow=workflow,
    )

    # WHEN the case is started
    with pytest.raises(CalledProcessError):
        analysis_starter.start(case_id)

    # THEN the error is propagated and the case should be set as not running
    mock_tracker.set_case_as_not_running.assert_called_once_with(case_id)


@pytest.mark.parametrize(
    "error_type",
    [HTTPError, SeqeraError],
)
def test_start_seqera_related_error_raised_in_run_and_track(error_type: type[Exception]):
    """Test that an error raised in submitting the analysis job is handled correctly."""
    # GIVEN a case_id
    case_id: str = "case_id"

    # GIVEN a submitter and a tracker
    submitter: SeqeraPlatformSubmitter = create_autospec(SeqeraPlatformSubmitter)
    tracker: TypedMock[NextflowTracker] = create_typed_mock(NextflowTracker)

    # GIVEN an analysis starter
    analysis_starter = AnalysisStarter(
        configurator=create_autospec(NextflowConfigurator),
        input_fetcher=create_autospec(FastqFetcher),
        store=create_autospec(Store),
        submitter=submitter,
        tracker=tracker.as_type,
        workflow=Workflow.RAREDISEASE,
    )

    # GIVEN that the submitter raises an error when submitting the analysis job
    submitter.submit = Mock(side_effect=error_type)

    # WHEN the case is started
    with pytest.raises(error_type):
        analysis_starter.start(case_id)

    # THEN the error is propagated and the case should be set as not running
    tracker.as_mock.set_case_as_not_running.assert_called_once_with(case_id)


@pytest.mark.parametrize(
    "workflow",
    [
        Workflow.BALSAMIC,
        Workflow.MICROSALT,
        Workflow.MIP_DNA,
        Workflow.RNAFUSION,
        Workflow.RAREDISEASE,
        Workflow.TAXPROFILER,
    ],
)
def test_run(
    workflow: Workflow,
    analysis_starter_scenario: dict,
):
    """Test that the case can be run successfully."""
    # GIVEN a case_id
    case_id: str = "case_id"

    # GIVEN a mock configurator, submitter, tracker, and case config
    mock_configurator, mock_case_config, mock_submitter, mock_tracker, submit_result = (
        analysis_starter_scenario[workflow]
    )

    mock_submitter.submit = Mock(return_value=submit_result)

    # GIVEN that the get_config method from the configurator returns the mock case config
    mock_configurator.get_config.return_value = mock_case_config

    # GIVEN an analysis starter initialised with the previously mocked classes
    analysis_starter = AnalysisStarter(
        configurator=mock_configurator,
        input_fetcher=create_autospec(FastqFetcher),
        store=create_autospec(Store),
        submitter=mock_submitter,
        tracker=mock_tracker,
        workflow=workflow,
    )

    # WHEN running the case
    analysis_starter.run(case_id)

    # THEN the tracker should ensure that the analysis is not ongoing
    mock_tracker.ensure_analysis_not_ongoing.assert_called_once_with(case_id)

    # THEN the tracker should set the case as running
    mock_tracker.set_case_as_running.assert_called_once_with(case_id)

    # THEN the analysis jobs should be submitted
    mock_submitter.submit.assert_called_once_with(mock_case_config)

    # THEN the tracker should track the case
    mock_tracker.track.assert_called_once_with(case_config=submit_result)
