import re

from cg.models.cg_config import CGConfig
from cg.services.post_processing.pacbio.post_processing_service import PacBioPostProcessingService


def get_post_processing_service_from_run_name(
    context: CGConfig, run_name: str
) -> PacBioPostProcessingService:
    """
    Get the correct post-processing service based on the run name.
    Raises:
        NameError if the run name is not recognized.
    """
    if _is_run_pacbio(run_name):
        return context.post_processing_services.pacbio
    raise NameError(f"Could not find a post-processing service for run name: {run_name}")


def _is_run_pacbio(run_name: str) -> bool:
    pattern: str = r"^r\d+_\d+_\d+/(1|2)_[^/]+$"
    return bool(re.match(pattern, run_name))
