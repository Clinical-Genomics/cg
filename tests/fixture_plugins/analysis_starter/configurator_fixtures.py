import pytest

from cg.apps.lims import LimsAPI
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.models.cg_config import CGConfig, RarediseaseConfig, RnafusionConfig
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
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
from cg.services.analysis_starter.configurator.implementations.balsamic import BalsamicConfigurator
from cg.services.analysis_starter.configurator.implementations.microsalt import (
    MicrosaltConfigurator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator
from cg.store.store import Store


@pytest.fixture
def microsalt_configurator(
    microsalt_config_file_creator: MicrosaltConfigFileCreator,
    cg_context: CGConfig,
    microsalt_fastq_handler: MicrosaltFastqHandler,
    lims_api: LimsAPI,
    microsalt_store: Store,
) -> MicrosaltConfigurator:
    return MicrosaltConfigurator(
        config_file_creator=microsalt_config_file_creator,
        fastq_handler=microsalt_fastq_handler,
        lims_api=lims_api,
        microsalt_config=cg_context.microsalt,
        store=microsalt_store,
    )


@pytest.fixture
def raredisease_configurator(
    raredisease_sample_sheet_creator: RarediseaseSampleSheetCreator,
    raredisease_params_file_creator: RarediseaseParamsFileCreator,
    mock_store_for_raredisease_file_creators: Store,
    nextflow_config_file_creator: NextflowConfigFileCreator,
    raredisease_extension: PipelineExtension,
    raredisease_config_object: RarediseaseConfig,
) -> NextflowConfigurator:
    return NextflowConfigurator(
        store=mock_store_for_raredisease_file_creators,
        config_file_creator=nextflow_config_file_creator,
        params_file_creator=raredisease_params_file_creator,
        pipeline_config=raredisease_config_object,
        sample_sheet_creator=raredisease_sample_sheet_creator,
        pipeline_extension=raredisease_extension,
    )


@pytest.fixture
def rnafusion_configurator(
    rnafusion_sample_sheet_creator: RNAFusionSampleSheetCreator,
    rnafusion_params_file_creator: RNAFusionParamsFileCreator,
    mock_store_for_rnafusion_sample_sheet_creator: Store,
    nextflow_config_file_creator: NextflowConfigFileCreator,
    rnafusion_config_object: RnafusionConfig,
) -> NextflowConfigurator:
    return NextflowConfigurator(
        store=mock_store_for_rnafusion_sample_sheet_creator,
        config_file_creator=nextflow_config_file_creator,
        params_file_creator=rnafusion_params_file_creator,
        pipeline_config=rnafusion_config_object,
        sample_sheet_creator=rnafusion_sample_sheet_creator,
        pipeline_extension=PipelineExtension(),
    )


@pytest.fixture
def balsamic_configurator(
    cg_context: CGConfig,
    lims_api: LimsAPI,
    base_store: Store,
) -> BalsamicConfigurator:

    return BalsamicConfigurator(
        config=cg_context.balsamic,
        lims_api=lims_api,
        store=base_store,
    )
