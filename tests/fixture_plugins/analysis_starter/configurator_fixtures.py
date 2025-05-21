import pytest

from cg.apps.lims import LimsAPI
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.models.cg_config import CGConfig
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
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
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
    raredisease_context: CGConfig,
    raredisease_config_file_creator: NextflowConfigFileCreator,
    raredisease_sample_sheet_creator: RarediseaseSampleSheetCreator,
    raredisease_params_file_creator: RarediseaseParamsFileCreator,
    raredisease_extension: PipelineExtension,
) -> NextflowConfigurator:
    return NextflowConfigurator(
        store=raredisease_context.status_db,
        pipeline_config=raredisease_context.raredisease,
        housekeeper_api=raredisease_context.housekeeper_api,
        lims=raredisease_context.lims_api,
        config_file_creator=raredisease_config_file_creator,
        sample_sheet_creator=raredisease_sample_sheet_creator,
        params_file_creator=raredisease_params_file_creator,
        pipeline_extension=raredisease_extension,
    )
