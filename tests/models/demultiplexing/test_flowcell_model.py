from pathlib import Path
from typing import Type

from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.constants.demultiplexing import BclConverter


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


def test_get_sample_model_bcl2fastq(bcl2fastq_flow_cell: FlowCellDirectoryData):
    """Test that the sample model of a bcl2fastq flow cell is FlowCellSampleNovaSeq6000Bcl2Fastq."""
    # GIVEN a Bcl2Fastq flow cell

    # WHEN getting the sample model
    sample_model: Type[FlowCellSampleBcl2Fastq] = bcl2fastq_flow_cell.sample_type

    # THEN it is FlowCellSampleNovaSeq6000Bcl2Fastq
    assert sample_model == FlowCellSampleBcl2Fastq


def test_get_sample_model_dragen(bcl_convert_flow_cell: FlowCellDirectoryData):
    """Test that the sample model of a dragen flow cell is FlowCellSampleBCLConvert."""
    # GIVEN a dragen flow cell

    # WHEN getting the sample model
    sample_model: Type[FlowCellSampleBCLConvert] = bcl_convert_flow_cell.sample_type

    # THEN it is FlowCellSampleNovaSeq6000Bcl2Fastq
    assert sample_model == FlowCellSampleBCLConvert


def test_get_sample_model_novaseq_x(novaseq_x_flow_cell: FlowCellDirectoryData):
    """Test that the sample model of a NovaSeqX flow cell is FlowCellSampleNovaSeqX."""
    # GIVEN a NovaSeqX flow cell

    # WHEN getting the sample model
    sample_model: Type[FlowCellSampleBCLConvert] = novaseq_x_flow_cell.sample_type

    # THEN it is FlowCellSampleNovaSeq6000Bcl2Fastq
    assert sample_model == FlowCellSampleBCLConvert


def test_get_bcl_converter_by_sequencer(
    flow_cell_directory_name_demultiplexed_with_bcl2fastq: str,
):
    """Test that the bcl converter of a bcl2fastq flow cell is bcl2fastq."""
    # GIVEN a Bcl2Fastq flow cell directory

    # WHEN instantiating a flow cell object
    flow_cell = FlowCellDirectoryData(
        flow_cell_path=Path(flow_cell_directory_name_demultiplexed_with_bcl2fastq)
    )

    # THEN it sets the converter to blc2fastq
    assert flow_cell.bcl_converter == BclConverter.BCL2FASTQ


def test_flow_cell_directory_data_with_set_bcl_converter(
    flow_cell_directory_name_demultiplexed_with_bcl2fastq: str, bcl_converter=BclConverter.DRAGEN
):
    """Test that the bcl converter is set to the specified value."""
    # GIVEN a Bcl2Fastq flow cell directory

    # GIVEN the bcl converter is set to dragen

    # WHEN instantiating a flow cell object
    flow_cell = FlowCellDirectoryData(
        flow_cell_path=Path(flow_cell_directory_name_demultiplexed_with_bcl2fastq),
        bcl_converter=bcl_converter,
    )

    # THEN the bcl converter is dragen
    assert flow_cell.bcl_converter == bcl_converter


def test_flow_cell_directory_data_with_novaseq_flow_cell_directory(
    flow_cell_directory_name_demultiplexed_with_bcl_convert: str,
):
    """Test that the bcl converter is set to dragen when prodiving a novaseq flow cell directory."""
    # GIVEN a Bcl2Fastq flow cell directory

    # WHEN instantiating a flow cell object
    flow_cell = FlowCellDirectoryData(
        flow_cell_path=Path(flow_cell_directory_name_demultiplexed_with_bcl_convert),
    )

    # THEN the bcl converter is dragen
    assert flow_cell.bcl_converter == BclConverter.DRAGEN
