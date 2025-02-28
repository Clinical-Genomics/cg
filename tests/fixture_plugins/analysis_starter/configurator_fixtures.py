import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.raredisease import (
    RarediseaseConfigurator,
)


@pytest.fixture
def raredisease_configurator(raredisease_context: CGConfig) -> RarediseaseConfigurator:
    return RarediseaseConfigurator(
        store=raredisease_context.status_db,
        config=raredisease_context.raredisease,
        housekeeper_api=raredisease_context.housekeeper_api,
        lims=raredisease_context.lims_api,
    )
