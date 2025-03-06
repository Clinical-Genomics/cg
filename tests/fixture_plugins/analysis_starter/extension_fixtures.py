import pytest

from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension


@pytest.fixture
def raredisease_extension() -> PipelineExtension:
    return PipelineExtension()
