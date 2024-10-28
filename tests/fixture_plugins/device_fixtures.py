"""Fixtures related to grouping all sequencing devices: PacBio, Illumina, ONT & Saphire."""

import pytest

from cg.models.cg_config import PostProcessingServices, RunNamesServices
from cg.services.run_devices.pacbio.post_processing_service import PacBioPostProcessingService
from cg.services.run_devices.run_names.pacbio import PacbioRunNamesService


@pytest.fixture
def post_processing_services(
    pac_bio_post_processing_service: PacBioPostProcessingService,
) -> PostProcessingServices:
    """Return the post processing services."""
    return PostProcessingServices(pacbio=pac_bio_post_processing_service)


@pytest.fixture
def run_names_services(pacbio_run_names_service: PacbioRunNamesService) -> RunNamesServices:
    """Return the run names services."""
    return RunNamesServices(pacbio=pacbio_run_names_service)
