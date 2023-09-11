import logging
from typing import List
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreator,
    SampleSheetCreatorBcl2Fastq,
    SampleSheetCreatorBCLConvert,
)
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.constants.demultiplexing import BclConverter
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)


def get_sample_sheet_creator(
    flow_cell: FlowCellDirectoryData,
    lims_samples: List[FlowCellSample],
    force: bool,
) -> SampleSheetCreator:
    """Returns an initialised sample sheet creator according to the software used for demultiplexing."""
    if flow_cell.bcl_converter == BclConverter.BCL2FASTQ:
        return SampleSheetCreatorBcl2Fastq(
            flow_cell=flow_cell, lims_samples=lims_samples, force=force
        )
    return SampleSheetCreatorBCLConvert(flow_cell=flow_cell, lims_samples=lims_samples, force=force)


def create_sample_sheet(
    flow_cell: FlowCellDirectoryData,
    lims_samples: List[FlowCellSample],
    force: bool = False,
) -> List[List[str]]:
    """Create a sample sheet for a flow cell."""
    sample_sheet_creator = get_sample_sheet_creator(
        flow_cell=flow_cell,
        lims_samples=lims_samples,
        force=force,
    )
    LOG.info(
        f"Constructing a {flow_cell.bcl_converter} sample sheet for the {flow_cell.sequencer_type} flow cell {flow_cell.id}"
    )
    return sample_sheet_creator.construct_sample_sheet()
