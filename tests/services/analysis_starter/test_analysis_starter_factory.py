from unittest.mock import MagicMock, Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.compress import CompressAPI
from cg.models.cg_config import (
    CGConfig,
    IlluminaConfig,
    MipConfig,
    RunInstruments,
    SeqeraPlatformConfig,
)
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories import starter_factory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.input_fetcher.implementations.bam_fetcher import BamFetcher
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.services.analysis_starter.service import AnalysisStarter
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.submitter import (
    SeqeraPlatformSubmitter,
)
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.services.analysis_starter.tracker.implementations.nextflow import NextflowTracker
from cg.store.store import Store


def test_analysis_starter_factory_microsalt(cg_context: CGConfig, mocker: MockerFixture):
    """Test that the AnalysisStarterFactory creates a Microsalt AnalysisStarter correctly."""
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


def test_analysis_starter_factory_mip_dna():
    # GIVEN a CGConfig with configuration info for MIP-DNA
    mip_rd_dna_config: MipConfig = create_autospec(
        MipConfig,
        root="root",
        conda_binary="conda/binary",
        conda_env="conda_env",
        mip_config="mip/config.config",
        workflow=Workflow.MIP_DNA,
        script="script",
    )
    cg_config: CGConfig = create_autospec(
        CGConfig,
        mip_rd_dna=mip_rd_dna_config,
        data_flow=Mock(),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )

    # GIVEN an AnalysisStarterFactory
    analysis_starter_factory = AnalysisStarterFactory(cg_config)

    # WHEN getting the analysis starter for MIP-DNA
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_workflow(
        Workflow.MIP_DNA
    )

    # THEN the analysis starter should have been configured correctly
    assert isinstance(analysis_starter.configurator, MIPDNAConfigurator)
    assert isinstance(analysis_starter.input_fetcher, FastqFetcher)
    assert isinstance(analysis_starter.submitter, SubprocessSubmitter)
    assert isinstance(analysis_starter.tracker, MIPDNATracker)


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
    """Test that the AnalysisStarterFactory creates a Nextflow AnalysisStarter correctly."""
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
    mock_client: SeqeraPlatformClient = create_autospec(SeqeraPlatformClient)
    mocker.patch.object(starter_factory, "SeqeraPlatformClient", return_value=mock_client)

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


def test_get_analysis_starter_for_workflow_nallo():
    cg_config = create_autospec(
        CGConfig,
        data_flow=Mock(),
        nallo=Mock(),  # TODO: Implement something meaningful here
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )
    analysis_starter_factory = AnalysisStarterFactory(cg_config)

    # WHEN calling get_analysis_starter_for_workflow with workflow Nallo
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_workflow(
        Workflow.NALLO
    )

    # THEN the analysis starter should be as expected
    assert isinstance(analysis_starter.input_fetcher, BamFetcher)
    assert isinstance(analysis_starter.configurator, NextflowConfigurator)
    assert isinstance(analysis_starter.submitter, SeqeraPlatformSubmitter)
    assert isinstance(analysis_starter.tracker, NextflowTracker)
