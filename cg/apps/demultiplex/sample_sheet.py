"""Create sample sheet for demultiplexing"""
import logging
from typing import List

from cg.apps.lims import LimsAPI
from cg.apps.lims.samplesheet import LimsFlowcellSample, sample_sheet

LOG = logging.getLogger(__name__)


def create_sample_sheet(
    lims: LimsAPI, flowcell_type: str, flowcell_name: str
) -> List[LimsFlowcellSample]:
    """Create a sample sheet based on information about samples in a flowcell from Lims"""
    lims_samples: List[LimsFlowcellSample] = list(sample_sheet(lims=lims, flowcell=flowcell_name))
    if not lims_samples:
        message = f"Could not find lims information for flowcell {flowcell_name}"
        LOG.warning(message)
        raise SyntaxError(message)

    return lims_samples
