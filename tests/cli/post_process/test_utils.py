import pytest

from cg.cli.post_process.utils import get_post_processing_service_from_run_name
from cg.models.cg_config import CGConfig
from cg.services.run_devices.pacbio.post_processing_service import PacBioPostProcessingService


def test_get_post_processing_service_from_run_name(
    pac_bio_context: CGConfig, pac_bio_sequencing_run_name: str
):
    """Test that a the correct post processing service is returned given a run name."""
    # GIVEN a context with a post-processing service for the run name
    assert pac_bio_context.post_processing_services.pacbio

    # WHEN getting the post-processing service from the run name
    service: PacBioPostProcessingService = get_post_processing_service_from_run_name(
        context=pac_bio_context, run_name=pac_bio_sequencing_run_name
    )
    # THEN a the correct post-processing service should be returned
    assert isinstance(service, PacBioPostProcessingService)


@pytest.mark.parametrize(
    "wrong_run_name",
    [
        "m_84202_2024_05_22_133539/1_A01",
        "r84202_20240522133539/1_A01",
        "r84202_20240522_133539/3_A01",
    ],
    ids=["doesn't start with r", "incorrect splits", "incorrect plate"],
)
def test_get_post_processing_service_from_wrong_run_name(
    pac_bio_context: CGConfig, wrong_run_name: str
):
    """Test that a the correct post processing service is returned given a run name."""
    # GIVEN a wrong run name

    # GIVEN a context with a post-processing service for the run name
    assert pac_bio_context.post_processing_services.pacbio

    # WHEN getting the post-processing service from the run name
    with pytest.raises(NameError):
        get_post_processing_service_from_run_name(context=pac_bio_context, run_name=wrong_run_name)

    # THEN an error is raised
