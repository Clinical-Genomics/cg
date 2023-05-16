import logging
from typing import List
from typing_extensions import Literal

from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import (
    SampleSheetCreatorV1,
    SampleSheetCreatorV2,
)
from cg.apps.lims.samplesheet import LimsFlowcellSample
from cg.constants.sequencing import Sequencers
from cg.constants.demultiplexing import BclConverter
from cg.exc import FlowCellError
from cg.models.demultiplex.flow_cell import FlowCell

LOG = logging.getLogger(__name__)


def create_sample_sheet(
    bcl_converter: Literal[BclConverter.BCL2FASTQ, BclConverter.DRAGEN],
    flow_cell: FlowCell,
    lims_samples: List[LimsFlowcellSample],
    force: bool = False,
) -> List[List[str]]:
    # TODO tests for this function
    """Create a sample sheet for a flow cell."""
    if flow_cell.sample_sheet_path.exists():
        message = f"Sample sheet {flow_cell.sample_sheet_path} already exists!"
        LOG.warning(message)
        raise FileExistsError(message)

    flow_cell_sequencer: str = flow_cell.sequencer_type

    if flow_cell_sequencer == Sequencers.NOVASEQ:
        sample_sheet_creator = SampleSheetCreatorV1(
            bcl_converter=bcl_converter,
            flow_cell=flow_cell,
            lims_samples=lims_samples,
            force=force,
        )
    elif flow_cell_sequencer == Sequencers.NOVASEQX:
        sample_sheet_creator = SampleSheetCreatorV2(
            flow_cell=flow_cell,
            lims_samples=lims_samples,
            force=force,
        )
    else:
        message = f"Only demultiplexing of Novaseq sequence data is currently supported. Found sequencer type: {flow_cell_sequencer}"
        LOG.warning(message)
        raise FlowCellError(message=message)

    return sample_sheet_creator.construct_sample_sheet()
