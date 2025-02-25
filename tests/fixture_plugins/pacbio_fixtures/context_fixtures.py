import pytest

from cg.models.cg_config import CGConfig, PostProcessingServices, RunNamesServices


@pytest.fixture
def pac_bio_context(
    cg_context: CGConfig,
    post_processing_services: PostProcessingServices,
    run_names_services: RunNamesServices,
) -> CGConfig:
    cg_context.post_processing_services_ = post_processing_services
    cg_context.run_names_services_ = run_names_services
    return cg_context
