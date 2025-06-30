import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.rnafusion import (
    RNAFusionParamsFileCreator,
)


@pytest.fixture
def raredisease_params_file_creator(
    raredisease_context: CGConfig,
) -> RarediseaseParamsFileCreator:
    return RarediseaseParamsFileCreator(
        store=raredisease_context.status_db,
        lims=raredisease_context.lims_api,
        params=raredisease_context.raredisease.params,
    )


@pytest.fixture
def rnafusion_params_file_creator(rnafusion_context: CGConfig) -> RNAFusionParamsFileCreator:
    return RNAFusionParamsFileCreator(rnafusion_context.rnafusion.params)
