import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.implementations.nextflow import NextflowConfigurator


@pytest.fixture
def nextflow_configurator(raredisease_context: CGConfig) -> NextflowConfigurator:
    return NextflowConfigurator(
        store=raredisease_context.status_db,
        config=raredisease_context.raredisease,
    )
