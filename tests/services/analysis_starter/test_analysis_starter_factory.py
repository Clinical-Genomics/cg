from unittest.mock import ANY, MagicMock, Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.meta.archive.archive import SpringArchiveAPI
from cg.meta.compress import CompressAPI
from cg.models.cg_config import (
    BalsamicConfig,
    CGConfig,
    CommonAppConfig,
    Encryption,
    IlluminaConfig,
    MipConfig,
    NextflowConfig,
    RunInstruments,
    SeqeraPlatformConfig,
)
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.mip_dna import MIPDNAConfigurator
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories import starter_factory
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.input_fetcher.implementations.bam_fetcher import BamFetcher
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_client import (
    SeqeraPlatformClient,
)
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_submitter import (
    SeqeraPlatformSubmitter,
)
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
from cg.services.analysis_starter.tracker.implementations.balsamic import BalsamicTracker
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.services.analysis_starter.tracker.implementations.nextflow_tracker import NextflowTracker
from cg.store.store import Store


def test_analysis_starter_factory_balsamic(cg_balsamic_config: BalsamicConfig):
    # GIVEN a CGConfig with configuration info for Balsamic
    cg_config: CGConfig = create_autospec(
        CGConfig,
        balsamic=cg_balsamic_config,
        data_flow=Mock(),
        encryption=create_autospec(Encryption, binary_path="encryption.bin"),
        pdc=create_autospec(CommonAppConfig, binary_path="pdc.bin"),
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )

    # GIVEN an AnalysisStarterFactory
    analysis_starter_factory = AnalysisStarterFactory(cg_config)

    # WHEN getting the analysis starter for Balsamic
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_workflow(
        Workflow.BALSAMIC
    )

    # THEN the analysis starter should have been configured correctly
    assert isinstance(analysis_starter.configurator, BalsamicConfigurator)
    assert isinstance(analysis_starter.input_fetcher, FastqFetcher)
    assert isinstance(analysis_starter.submitter, SubprocessSubmitter)
    assert isinstance(analysis_starter.tracker, BalsamicTracker)


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
        encryption=create_autospec(Encryption, binary_path="encryption.bin"),
        pdc=create_autospec(CommonAppConfig, binary_path="pdc.bin"),
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
    "workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION, Workflow.TAXPROFILER, Workflow.TOMTE]
)
def test_get_analysis_starter_for_workflow_nextflow_fastq(
    nextflow_root: str,
    raredisease_config_object: NextflowConfig,
    rnafusion_config_object: NextflowConfig,
    seqera_platform_config: SeqeraPlatformConfig,
    taxprofiler_config_object: NextflowConfig,
    tomte_config_object: NextflowConfig,
    workflow: Workflow,
    mocker: MockerFixture,
):
    """
    Test that the AnalysisStarterFactory creates a correct AnalysisStarter instance.
    This test uses fixtures from raredisease but is valid for all Nextflow workflows
    that require FASTQ input fetching:
     - raredisease
     - RNAFUSION
     - Taxprofiler
     - Tomte
    """
    # GIVEN a CGConfig with valid Seqera platform, data flow and Nextflow pipeline configurations
    cg_config: CGConfig = create_autospec(
        CGConfig,
        data_flow=Mock(),
        encryption=create_autospec(Encryption, binary_path="encryption.bin"),
        pdc=create_autospec(CommonAppConfig, binary_path="pdc.bin"),
        raredisease=raredisease_config_object,
        rnafusion=rnafusion_config_object,
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
        seqera_platform=seqera_platform_config,
        taxprofiler=taxprofiler_config_object,
        tomte=tomte_config_object,
    )

    # GIVEN an AnalysisStarterFactory
    analysis_starter_factory = AnalysisStarterFactory(cg_config)

    # GIVEN a SeqeraPlatformSubmitter constructor and a SeqeraPlatformClient
    mock_platform_submitter_init: MagicMock = mocker.spy(SeqeraPlatformSubmitter, "__init__")
    mock_client: SeqeraPlatformClient = create_autospec(SeqeraPlatformClient)
    mocker.patch.object(starter_factory, "SeqeraPlatformClient", return_value=mock_client)

    # GIVEN a NextflowTracker constructor
    mock_tracker_init: MagicMock = mocker.spy(NextflowTracker, "__init__")

    # GIVEN SpringArchiveAPI and CompressAPI constructors
    mock_archive_api_init: MagicMock = mocker.spy(SpringArchiveAPI, "__init__")
    mock_compress_api_init: MagicMock = mocker.spy(CompressAPI, "__init__")

    # WHEN fetching the AnalysisStarter for a Nextflow workflow
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_workflow(
        workflow
    )

    # THEN the AnalysisStarter should have a Nextflow configurator
    assert isinstance(analysis_starter.configurator, NextflowConfigurator)

    # THEN the factory should have created a FastqFetcher correctly
    assert isinstance(analysis_starter.input_fetcher, FastqFetcher)
    mock_archive_api_init.assert_called_once_with(
        ANY,
        status_db=cg_config.status_db,
        housekeeper_api=cg_config.housekeeper_api,
        data_flow_config=cg_config.data_flow,
    )
    mock_compress_api_init.assert_called_once_with(
        ANY,
        backup_api=ANY,
        hk_api=cg_config.housekeeper_api,
        crunchy_api=cg_config.crunchy_api,
        demux_root=cg_config.run_instruments.illumina.demultiplexed_runs_dir,
    )

    # THEN the AnalysisStarter should have a correct Store
    assert analysis_starter.store == cg_config.status_db

    # THEN the factory should have created a SeqeraPlatformSubmitter correctly
    assert isinstance(analysis_starter.submitter, SeqeraPlatformSubmitter)
    mock_platform_submitter_init.assert_called_once_with(
        ANY,
        client=mock_client,
        compute_environment_ids=cg_config.seqera_platform.compute_environments,
    )

    # THEN the factory should have created a NextflowTracker correctly
    assert isinstance(analysis_starter.tracker, NextflowTracker)
    mock_tracker_init.assert_called_once_with(
        ANY,
        store=cg_config.status_db,
        trailblazer_api=cg_config.trailblazer_api,
        workflow_root=nextflow_root,
    )


def test_get_analysis_starter_for_workflow_nallo(
    nallo_config_object: NextflowConfig,
    mocker: MockerFixture,
):
    """Test that the AnalysisStarterFactory creates a Nallo AnalysisStarter correctly."""
    # GIVEN a CGConfig with a Nallo pipeline configuration
    cg_config: CGConfig = create_autospec(
        CGConfig,
        nallo=nallo_config_object,
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
        seqera_platform=Mock(),
    )

    # GIVEN an AnalysisStarterFactory
    analysis_starter_factory = AnalysisStarterFactory(cg_config)

    # GIVEN a BamFetcher constructor
    mock_fetcher_init: MagicMock = mocker.spy(BamFetcher, "__init__")

    # WHEN fetching the AnalysisStarter
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_workflow(
        Workflow.NALLO
    )

    # THEN the AnalysisStarter should have a Nextflow configurator
    assert isinstance(analysis_starter.configurator, NextflowConfigurator)

    # THEN the AnalysisStarter should have created a BamFetcher correctly
    assert isinstance(analysis_starter.input_fetcher, BamFetcher)
    mock_fetcher_init.assert_called_once_with(
        ANY, housekeeper_api=cg_config.housekeeper_api, status_db=cg_config.status_db
    )

    # THEN the factory should have created a SeqeraPlatformSubmitter correctly
    assert isinstance(analysis_starter.submitter, SeqeraPlatformSubmitter)

    # THEN the factory should have created a NextflowTracker correctly
    assert isinstance(analysis_starter.tracker, NextflowTracker)
