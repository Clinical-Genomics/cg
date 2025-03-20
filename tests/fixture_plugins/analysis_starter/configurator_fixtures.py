import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.raredisease import (
    RarediseaseSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator


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
