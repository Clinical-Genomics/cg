from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.models.cg_config import CGConfig, SeqeraPlatformConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.rnafusion import (
    RNAFusionSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.input_fetcher.implementations.fastq_fetcher import FastqFetcher
from cg.services.analysis_starter.service import AnalysisStarter
from cg.services.analysis_starter.submitters.seqera_platform.submitter import (
    SeqeraPlatformSubmitter,
)
from cg.services.analysis_starter.submitters.subprocess.submitter import SubprocessSubmitter
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


def test_analysis_starter_factory_raredisease(
    cg_context: CGConfig, seqera_platform_config: SeqeraPlatformConfig, mocker: MockerFixture
):
    # GIVEN an AnalysisStarterFactory
    analysis_starter_factory = AnalysisStarterFactory(cg_context)

    # GIVEN that the CGConfig has the seqera platform config set
    cg_context.seqera_platform = seqera_platform_config

    # GIVEN a Raredisease case
    mocker.patch.object(Store, "get_case_workflow", return_value=Workflow.RAREDISEASE)

    # WHEN fetching the AnalysisStarter
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_case(
        "case_id"
    )

    # THEN the Factory should have it configured correctly
    assert isinstance(analysis_starter.configurator, NextflowConfigurator)
    assert isinstance(
        analysis_starter.configurator.sample_sheet_creator, RarediseaseSampleSheetCreator
    )
    assert isinstance(
        analysis_starter.configurator.params_file_creator, RarediseaseParamsFileCreator
    )
    assert isinstance(analysis_starter.input_fetcher, FastqFetcher)
    assert isinstance(analysis_starter.submitter, SeqeraPlatformSubmitter)


def test_analysis_starter_factory_rnafusion(
    cg_context: CGConfig, seqera_platform_config: SeqeraPlatformConfig, mocker: MockerFixture
):
    # GIVEN an AnalysisStarterFactory
    analysis_starter_factory = AnalysisStarterFactory(cg_context)

    # GIVEN that the CGConfig has the seqera platform config set
    cg_context.seqera_platform = seqera_platform_config

    # GIVEN an RNAFusion case
    mocker.patch.object(Store, "get_case_workflow", return_value=Workflow.RNAFUSION)

    # WHEN fetching the AnalysisStarter
    analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_case(
        "case_id"
    )

    # THEN the Factory should have it configured correctly
    assert isinstance(analysis_starter.configurator, NextflowConfigurator)
    assert isinstance(
        analysis_starter.configurator.sample_sheet_creator, RNAFusionSampleSheetCreator
    )
    assert isinstance(analysis_starter.configurator.params_file_creator, RNAFusionParamsFileCreator)
    assert isinstance(analysis_starter.input_fetcher, FastqFetcher)
    assert isinstance(analysis_starter.submitter, SeqeraPlatformSubmitter)
