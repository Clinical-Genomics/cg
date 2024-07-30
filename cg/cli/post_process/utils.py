import re

from cg.models.cg_config import CGConfig
from cg.services.post_processing.pacbio.post_processing_service import PacBioPostProcessingService

PATTERN_TO_DEVICE_MAP: dict[str, str] = {
    r"^r\d+_\d+_\d+/(1|2)_[^/]+$": "pacbio",
}


def get_post_processing_service_from_run_name(
    context: CGConfig, run_name: str
) -> PacBioPostProcessingService:
    """
    Get the correct post-processing service based on the run name.
    Raises:
        NameError if the run name is not recognized.
    """
    for pattern in PATTERN_TO_DEVICE_MAP.keys():
        if re.match(pattern, run_name):
            device: str = PATTERN_TO_DEVICE_MAP[pattern]
            return getattr(context.post_processing_services, device)
    raise NameError(f"Could not find a post-processing service for run name: {run_name}")
