"""Create a sample sheet"""
import logging
from typing import Iterable, List

from cg.apps.demultiplex.flowcell import Flowcell
from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.lims import LimsAPI
from cg.apps.lims.samplesheet import LimsFlowcellSample, flowcell_samples

LOG = logging.getLogger(__name__)


def sample_sheet(lims_samples: List[LimsFlowcellSample], flowcell: Flowcell) -> str:
    """Create a sample sheet based"""
