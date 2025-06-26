import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.params_file.raredisease import (
    RarediseaseParamsFileCreator,
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
