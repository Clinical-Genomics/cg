from pathlib import Path
from typing import Type

from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleNovaSeq6000Bcl2Fastq,
    FlowCellSampleNovaSeq6000Dragen,
    FlowCellSampleNovaSeqX,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


def test_flowcell_id(bcl2fastq_flow_cell_dir: Path):
    """Test parsing of flow cell id."""
    # GIVEN the path to a finished flow cell run
    # GIVEN the flow cell id
    flowcell_id: str = bcl2fastq_flow_cell_dir.name.split("_")[-1][1:]

    # WHEN instantiating a flow cell object
    flowcell_obj = FlowCellDirectoryData(flow_cell_path=bcl2fastq_flow_cell_dir)

    # THEN assert that the flow cell id is parsed
    assert flowcell_obj.id == flowcell_id


def test_flowcell_position(bcl2fastq_flow_cell_dir: Path):
    """Test getting flow cell position."""
    # GIVEN the path to a finished flow cell
    # GIVEN a flow cell object
    flowcell_obj = FlowCellDirectoryData(flow_cell_path=bcl2fastq_flow_cell_dir)

    # WHEN fetching the flow cell position
    position = flowcell_obj.position

    # THEN assert it is A or B
    assert position in ["A", "B"]


def test_rta_exists(bcl2fastq_flow_cell: FlowCellDirectoryData):
    """Test return of RTS file."""
    # GIVEN the path to a finished flow cell
    # GIVEN a flow cell object

    # WHEN fetching the path to the RTA file
    rta_file: Path = bcl2fastq_flow_cell.rta_complete_path

    # THEN assert that the file exists
    assert rta_file.exists()


def test_is_hiseq_x_copy_completed_ready(bcl2fastq_flow_cell: FlowCellDirectoryData):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flow cell object
    # GIVEN a copy complete file

    # WHEN fetching the path to the copy complete file
    is_completed = bcl2fastq_flow_cell.is_hiseq_x_copy_completed()

    # THEN assert that the file exists
    assert is_completed is True


def test_is_hiseq_x_delivery_started_ready(
    bcl2fastq_flow_cell: FlowCellDirectoryData, demultiplexing_delivery_file: Path
):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flow cell object
    # GIVEN a delivery file
    demultiplexing_delivery_file.touch()

    # WHEN checking the path to the delivery file
    is_delivered = bcl2fastq_flow_cell.is_hiseq_x_delivery_started()

    demultiplexing_delivery_file.unlink()

    # THEN assert that the file exists
    assert is_delivered is True


def test_is_hiseq_x_delivery_started_not_ready(bcl2fastq_flow_cell: FlowCellDirectoryData):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flow cell object

    # WHEN checking the path to the copy complete file
    is_delivered = bcl2fastq_flow_cell.is_hiseq_x_delivery_started()

    # THEN assert that the file do not exist
    assert is_delivered is False


def test_is_hiseq_x(bcl2fastq_flow_cell: FlowCellDirectoryData, hiseq_x_tile_dir: Path):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flow cell object
    # GIVEN a Hiseq X directory
    hiseq_x_tile_dir.mkdir(exist_ok=True)

    # WHEN checking the path to the Hiseq X flow cell directory
    is_hiseq_x = bcl2fastq_flow_cell.is_hiseq_x()

    # Clean up
    hiseq_x_tile_dir.rmdir()

    # THEN assert that the file exists
    assert is_hiseq_x is True


def test_get_sample_model_bcl2fastq(bcl2fastq_flow_cell: FlowCellDirectoryData):
    """Test that the sample model of a bcl2fastq flow cell is FlowCellSampleNovaSeq6000Bcl2Fastq."""
    # GIVEN a Bcl2Fastq flow cell

    # WHEN getting the sample model
    sample_model: Type[FlowCellSampleNovaSeq6000Bcl2Fastq] = bcl2fastq_flow_cell.sample_type

    # THEN it is FlowCellSampleNovaSeq6000Bcl2Fastq
    assert sample_model == FlowCellSampleNovaSeq6000Bcl2Fastq


def test_get_sample_model_dragen(dragen_flow_cell: FlowCellDirectoryData):
    """Test that the sample model of a dragen flow cell is FlowCellSampleNovaSeq6000Dragen."""
    # GIVEN a dragen flow cell

    # WHEN getting the sample model
    sample_model: Type[FlowCellSampleNovaSeq6000Dragen] = dragen_flow_cell.sample_type

    # THEN it is FlowCellSampleNovaSeq6000Bcl2Fastq
    assert sample_model == FlowCellSampleNovaSeq6000Dragen


def test_get_sample_model_novaseq_x(novaseq_x_flow_cell: FlowCellDirectoryData):
    """Test that the sample model of a NovaSeqX flow cell is FlowCellSampleNovaSeqX."""
    # GIVEN a NovaSeqX flow cell

    # WHEN getting the sample model
    sample_model: Type[FlowCellSampleNovaSeqX] = novaseq_x_flow_cell.sample_type

    # THEN it is FlowCellSampleNovaSeq6000Bcl2Fastq
    assert sample_model == FlowCellSampleNovaSeqX
