from unittest.mock import MagicMock, Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig, SeqeraPlatformConfig
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.services.analysis_starter.service import AnalysisStarter
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.submitter import (
    SeqeraPlatformSubmitter,
)
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.implementations.nextflow import NextflowTracker
from cg.store.store import Store


def test_analysis_starter_factory_microsalt(cg_context: CGConfig, mocker: MockerFixture):
    # GIVEN an AnalysisStarterFactory
    analysis_starter_factory = AnalysisStarterFactory(cg_context)

    # GIVEN a microSALT case
    mocker.patch.object(Store, "get_case_workflow", return_value=Workflow.MICROSALT)

    # WHEN fetching the AnalysisStarter
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_case(
        "case_id"
    )

    # THEN the Factory should have it configured correctly
    assert isinstance(analysis_starter.configurator, MicrosaltConfigurator)
    assert isinstance(analysis_starter.input_fetcher, FastqFetcher)
    assert isinstance(analysis_starter.submitter, SubprocessSubmitter)


@pytest.mark.parametrize(
    "workflow",
    [Workflow.RNAFUSION, Workflow.RAREDISEASE, Workflow.TAXPROFILER],
)
def test_analysis_starter_factory_nextflow_starter(
    cg_context: CGConfig,
    workflow: Workflow,
    seqera_platform_config: SeqeraPlatformConfig,
    mocker: MockerFixture,
):
    # GIVEN an AnalysisStarterFactory
    analysis_starter_factory = AnalysisStarterFactory(cg_context)

    # GIVEN that the CGConfig has the seqera platform config set
    cg_context.seqera_platform = seqera_platform_config

    # GIVEN a case with a Nextflow workflow
    mocker.patch.object(Store, "get_case_workflow", return_value=workflow)

    # GIVEN a mock for the SeqeraPlatformSubmitter constructor and a mocked SeqeraPlatformClient
    mock_platform_submitter_init: MagicMock = mocker.patch.object(
        SeqeraPlatformSubmitter, "__init__", return_value=None
    )
    mock_client: Mock[SeqeraPlatformClient] = create_autospec(SeqeraPlatformClient)
    mocker.patch(
        "cg.services.analysis_starter.factories.starter_factory.SeqeraPlatformClient",
        return_value=mock_client,
    )

    # GIVEN a NextflowTracker mocked constructor
    mock_tracker_init: MagicMock = mocker.patch.object(
        NextflowTracker, "__init__", return_value=None
    )

    # GIVEN mocks for the SpringArchiveAPI and CompressAPI constructors
    mock_archive_api_init: MagicMock = mocker.patch.object(
        SpringArchiveAPI, "__init__", return_value=None
    )
    mock_compress_api_init: MagicMock = mocker.patch.object(
        CompressAPI, "__init__", return_value=None
    )

    # WHEN fetching the AnalysisStarter
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_case(
        "case_id"
    )

    # THEN the AnalysisStarter should have a Nextflow configurator
    assert isinstance(analysis_starter.configurator, NextflowConfigurator)

    # THEN the factory should have created a FastqFetcher correctly
    assert isinstance(analysis_starter.input_fetcher, FastqFetcher)
    mock_archive_api_init.assert_called_once_with(
        status_db=cg_context.status_db,
        housekeeper_api=cg_context.housekeeper_api,
        data_flow_config=cg_context.data_flow,
    )
    mock_compress_api_init.assert_called_once_with(
        hk_api=cg_context.housekeeper_api,
        crunchy_api=cg_context.crunchy_api,
        demux_root=cg_context.run_instruments.illumina.demultiplexed_runs_dir,
    )

    # THEN the AnalysisStarter should have a correct Store
    assert analysis_starter.store == cg_context.status_db

    # THEN the factory should have created a SeqeraPlatformSubmitter correctly
    assert isinstance(analysis_starter.submitter, SeqeraPlatformSubmitter)
    mock_platform_submitter_init.assert_called_once_with(
        client=mock_client,
        compute_environment_ids=cg_context.seqera_platform.compute_environments,
    )

    # THEN the factory should have created a NextflowTracker correctly
    assert isinstance(analysis_starter.tracker, NextflowTracker)
    mock_tracker_init.assert_called_once_with(
        store=cg_context.status_db,
        trailblazer_api=cg_context.trailblazer_api,
        workflow_root=getattr(cg_context, workflow).root,
    )
