from pathlib import Path
from typing import Type

import pytest

from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.cli.demultiplex.copy_novaseqx_demultiplex_data import get_latest_analysis_path
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


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


def test_get_run_parameters_when_non_existing(demultiplexed_runs: Path):
    # GIVEN a flowcell object with a directory without run parameters
    flowcell_path: Path = Path(
        demultiplexed_runs,
        "201203_D00483_0200_AHVKJCDRXX",
    )
    flow_cell = FlowCellDirectoryData(flow_cell_path=flowcell_path)
    assert flow_cell.run_parameters_path.exists() is False

    # WHEN fetching the run parameters object
    with pytest.raises(FileNotFoundError):
        # THEN assert that a FileNotFound error is raised
        flow_cell.run_parameters


def test_has_demultiplexing_started_locally_false(tmp_flow_cell_directory_bclconvert: Path):
    # GIVEN a flow cell without a demuxstarted.txt file
    flow_cell = FlowCellDirectoryData(tmp_flow_cell_directory_bclconvert)
    assert not Path(flow_cell.path, DemultiplexingDirsAndFiles.DEMUX_STARTED).exists()

    # WHEN checking if the flow cell has started demultiplexing
    has_demux_started: bool = flow_cell.has_demultiplexing_started_locally()

    # THEN the response should be False
    assert not has_demux_started


def test_has_demultiplexing_started_locally_true(
    tmp_flow_cell_directory_bclconvert: Path,
):
    # GIVEN a flow cell with a demuxstarted.txt file
    flow_cell = FlowCellDirectoryData(tmp_flow_cell_directory_bclconvert)
    Path(flow_cell.path, DemultiplexingDirsAndFiles.DEMUX_STARTED).touch()

    # WHEN checking if the flow cell has started demultiplexing
    has_demux_started: bool = flow_cell.has_demultiplexing_started_locally()

    # THEN the response should be True
    assert has_demux_started


def test_has_demultiplexing_started_on_sequencer_true(
    novaseqx_flow_cell_dir_with_analysis_data: Path,
):
    # GIVEN a flow cell with a BCLConvert folder
    flow_cell = FlowCellDirectoryData(novaseqx_flow_cell_dir_with_analysis_data)
    Path.mkdir(
        Path(
            flow_cell.path,
            get_latest_analysis_path(flow_cell.path),
            DemultiplexingDirsAndFiles.DATA,
            DemultiplexingDirsAndFiles.BCL_CONVERT,
        )
    )

    # WHEN checking if the flow cell has started demultiplexing
    has_demux_started: bool = flow_cell.has_demultiplexing_started_on_sequencer()

    # THEN the response should be True
    assert has_demux_started


def test_has_demultiplexing_started_on_sequencer_false(
    novaseqx_flow_cell_dir_with_analysis_data: Path,
):
    # GIVEN a flow cell without a BCLConvert folder
    flow_cell = FlowCellDirectoryData(novaseqx_flow_cell_dir_with_analysis_data)
    assert not Path(
        flow_cell.path,
        get_latest_analysis_path(flow_cell.path),
        DemultiplexingDirsAndFiles.DATA,
        DemultiplexingDirsAndFiles.BCL_CONVERT,
    ).exists()

    # WHEN checking if the flow cell has started demultiplexing
    has_demux_started: bool = flow_cell.has_demultiplexing_started_on_sequencer()

    # THEN the response should be False
    assert not has_demux_started
