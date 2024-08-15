import pytest

from cg.models.cg_config import CGConfig, PostProcessingServices


@pytest.fixture
def pac_bio_context(
    cg_context: CGConfig, post_processing_services: PostProcessingServices
) -> CGConfig:
    cg_context.post_processing_services_ = post_processing_services
    return cg_context
