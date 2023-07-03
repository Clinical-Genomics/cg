import logging
from typing import List
from typing_extensions import Literal

from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreator,
    SampleSheetCreatorV1,
    SampleSheetCreatorV2,
)
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.constants.sequencing import Sequencers
from cg.constants.demultiplexing import BclConverter
from cg.exc import FlowCellError
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)


def sample_sheet_creator_factory(
    sequencer: str,
    bcl_converter: str,
    flow_cell: FlowCellDirectoryData,
    lims_samples: List[FlowCellSample],
    force: bool,
) -> SampleSheetCreator:
    """Returns an initialised sample sheet creator according to the sequencer."""
    if sequencer == Sequencers.NOVASEQ:
        return SampleSheetCreatorV1(
            bcl_converter=bcl_converter, flow_cell=flow_cell, lims_samples=lims_samples, force=force
        )
    elif sequencer == Sequencers.NOVASEQX:
        return SampleSheetCreatorV2(
            bcl_converter=bcl_converter, flow_cell=flow_cell, lims_samples=lims_samples, force=force
        )
    else:
        raise ValueError(f"Unsupported sequencer type: {sequencer}")


def create_sample_sheet(
    bcl_converter: Literal[BclConverter.BCL2FASTQ, BclConverter.DRAGEN],
    flow_cell: FlowCellDirectoryData,
    lims_samples: List[FlowCellSample],
    force: bool = False,
) -> List[List[str]]:
    """Create a sample sheet for a flow cell."""
    flow_cell_sequencer: str = flow_cell.sequencer_type
    try:
        sample_sheet_creator = sample_sheet_creator_factory(
            sequencer=flow_cell_sequencer,
            bcl_converter=bcl_converter,
            flow_cell=flow_cell,
            lims_samples=lims_samples,
            force=force,
        )
    except ValueError:
        message = (
            "Only NovaSeq and NovaSeqX sample sheets are currently supported."
            + f"Found sequencer type: {flow_cell_sequencer}"
        )
        LOG.warning(message)
        raise FlowCellError(message=message)
    LOG.info(
        f"Constructing a {bcl_converter} sample sheet for the {flow_cell_sequencer} flow cell {flow_cell.id}"
    )
    return sample_sheet_creator.construct_sample_sheet()


def create_sample_sheet2(
    bcl_converter: Literal[BclConverter.BCL2FASTQ, BclConverter.DRAGEN],
    flow_cell: FlowCellDirectoryData,
    lims_samples: List[FlowCellSample],
    force: bool = False,
) -> List[List[str]]:
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
            bcl_converter=bcl_converter,
            flow_cell=flow_cell,
            lims_samples=lims_samples,
            force=force,
        )
    else:
        message = f"Only demultiplexing of Novaseq sequence data is currently supported. Found sequencer type: {flow_cell_sequencer}"
        LOG.warning(message)
        raise FlowCellError(message=message)

    LOG.info(
        f"Constructing a {bcl_converter} sample sheet for the {flow_cell_sequencer} flow cell {flow_cell.id}"
    )
    return sample_sheet_creator.construct_sample_sheet()
