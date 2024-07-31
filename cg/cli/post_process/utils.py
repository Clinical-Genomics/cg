from cg.models.cg_config import CGConfig
from cg.services.post_processing.pacbio.post_processing_service import PacBioPostProcessingService
from cg.utils.mapping import get_item_by_pattern_in_source

PATTERN_TO_DEVICE_MAP: dict[str, str] = {
    r"^r\d+_\d+_\d+/(1|2)_[^/]+$": "pacbio",
}


def get_post_processing_service_from_run_name(
    context: CGConfig, run_name: str
) -> PacBioPostProcessingService:
    """Get the correct post-processing service based on the run name."""
    device: str = get_item_by_pattern_in_source(source=run_name, pattern_map=PATTERN_TO_DEVICE_MAP)
    return getattr(context.post_processing_services, device)
