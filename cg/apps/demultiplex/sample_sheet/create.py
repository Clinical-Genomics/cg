import logging
from typing import List

from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.lims.samplesheet import LimsFlowcellSample
from cg.exc import FlowcellError
from cg.models.demultiplex.run_parameters import RunParameters
from cg.store.models import Flowcell

LOG = logging.getLogger(__name__)


def create_sample_sheet(
    flowcell: Flowcell, lims_samples: List[LimsFlowcellSample], bcl_converter: str
) -> str:
    """Create a sample sheet for a flowcell"""
    if flowcell.sample_sheet_path.exists():
        message = f"Sample sheet {flowcell.sample_sheet_path} already exists!"
        LOG.warning(message)
        raise FileExistsError(message)

    run_parameters: RunParameters = flowcell.run_parameters_object

    if run_parameters.flowcell_type != "novaseq":
        message = f"Can only demultiplex novaseq with cg. Found type {run_parameters.flowcell_type}"
        LOG.warning(message)
        raise FlowcellError(message=message)

    sample_sheet_creator = SampleSheetCreator(
        flowcell_id=flowcell.flowcell_id,
        lims_samples=lims_samples,
        run_parameters=run_parameters,
        bcl_converter=bcl_converter,
    )
    return sample_sheet_creator.construct_sample_sheet()
