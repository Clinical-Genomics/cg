"""Fixtures related to grouping all sequencing devices: PacBio, Illumina, ONT & Saphire."""

import pytest

from cg.models.cg_config import PostProcessingServices
from cg.services.run_devices.pacbio.post_processing_service import PacBioPostProcessingService


@pytest.fixture
def post_processing_services(
    pac_bio_post_processing_service: PacBioPostProcessingService,
) -> PostProcessingServices:
    """Return the post processing services."""
    return PostProcessingServices(
        pacbio=pac_bio_post_processing_service,
    )
