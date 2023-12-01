import logging

from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreator,
    SampleSheetCreatorBcl2Fastq,
    SampleSheetCreatorBCLConvert,
)
from cg.constants.demultiplexing import BclConverter
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)


def get_sample_sheet_creator(
    flow_cell: FlowCellDirectoryData,
    lims_samples: list[FlowCellSample],
    force: bool,
) -> SampleSheetCreator:
    """Returns an initialised sample sheet creator according to the demultiplexing software."""
    if flow_cell.bcl_converter == BclConverter.BCL2FASTQ:
        return SampleSheetCreatorBcl2Fastq(
            flow_cell=flow_cell, lims_samples=lims_samples, force=force
        )
    return SampleSheetCreatorBCLConvert(flow_cell=flow_cell, lims_samples=lims_samples, force=force)


def create_sample_sheet(
    flow_cell: FlowCellDirectoryData,
    lims_samples: list[FlowCellSample],
    force: bool = False,
) -> list[list[str]]:
    """Create a sample sheet for a flow cell."""
    sample_sheet_creator: SampleSheetCreator = get_sample_sheet_creator(
        flow_cell=flow_cell,
        lims_samples=lims_samples,
        force=force,
    )
    LOG.info(
        f"Constructing a {flow_cell.bcl_converter} sample sheet for the {flow_cell.sequencer_type} flow cell {flow_cell.id}"
    )
    return sample_sheet_creator.construct_sample_sheet()
