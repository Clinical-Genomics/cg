from cg.cli.post_process.utils import get_post_processing_service_from_run_name
from cg.models.cg_config import CGConfig
from cg.services.post_processing.pacbio import PacBioPostProcessingService


def test_get_post_processing_service_from_run_name(
    pac_bio_context: CGConfig, pac_bio_sequencing_run_name: str
):
    """Test the function that gets the post-processing service from the run name."""
    # GIVEN a context with a post-processing service for the run name
    assert pac_bio_context.post_processing_services.pacbio

    # WHEN getting the post-processing service from the run name
    service: PacBioPostProcessingService = get_post_processing_service_from_run_name(
        context=pac_bio_context, run_name=pac_bio_sequencing_run_name
    )
    # THEN the correct post-processing service should be returned
    assert isinstance(service, PacBioPostProcessingService)
