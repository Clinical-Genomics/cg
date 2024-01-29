from pathlib import Path
from typing import Type

import pytest
from _pytest.fixtures import FixtureRequest

from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.cli.demultiplex.copy_novaseqx_demultiplex_data import get_latest_analysis_path
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.sequencing import Sequencers
from cg.exc import FlowCellError
from cg.models.demultiplex.run_parameters import RunParameters
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


def test_flow_cell_id(bcl2fastq_flow_cell_dir: Path):
    """Test parsing of flow cell id."""
    # GIVEN the path to a finished flow cell run
    # GIVEN the flow cell id
    flowcell_id: str = bcl2fastq_flow_cell_dir.name.split("_")[-1][1:]

    # WHEN instantiating a flow cell object
    flowcell_obj = FlowCellDirectoryData(flow_cell_path=bcl2fastq_flow_cell_dir)

    # THEN assert that the flow cell id is parsed
    assert flowcell_obj.id == flowcell_id


def test_flow_cell_position(bcl2fastq_flow_cell_dir: Path):
    """Test getting flow cell position."""
    # GIVEN the path to a finished flow cell
    # GIVEN a flow cell object
    flow_cell = FlowCellDirectoryData(flow_cell_path=bcl2fastq_flow_cell_dir)

    # WHEN fetching the flow cell position
    position = flow_cell.position

    # THEN assert it is A or B
    assert position in ["A", "B"]


def test_rta_exists(novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq: FlowCellDirectoryData):
    """Test return of RTS file."""
    # GIVEN the path to a finished flow cell
    # GIVEN a flow cell object

    # WHEN fetching the path to the RTA file
    rta_file: Path = novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq.rta_complete_path

    # THEN assert that the file exists
    assert rta_file.exists()


@pytest.mark.parametrize(
    "flow_cell_fixture_name, model",
    [
        ("novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq", FlowCellSampleBcl2Fastq),
        ("novaseq_6000_post_1_5_kits_flow_cell", FlowCellSampleBCLConvert),
        ("novaseq_x_flow_cell", FlowCellSampleBCLConvert),
    ],
)
def test_get_sample_model(
    flow_cell_fixture_name: str,
    model: Type[FlowCellSampleBcl2Fastq | FlowCellSampleBCLConvert],
    request: FixtureRequest,
):
    """Test getting the sample model of a flow cell returns the correct value."""
    # GIVEN a flow cell
    flow_cell: FlowCellDirectoryData = request.getfixturevalue(flow_cell_fixture_name)

    # WHEN getting the sample model
    sample_model: Type[FlowCellSampleBcl2Fastq | FlowCellSampleBCLConvert] = flow_cell.sample_type

    # THEN it is the expected model
    assert sample_model == model


def test_get_bcl_converter_default(
    flow_cell_directory_name_demultiplexed_with_bcl_convert: str,
):
    """Test that BCLConvert is the bcl converter set as default when instantiating a flow cell."""
    # GIVEN a flow cell directory

    # WHEN instantiating a flow cell object
    flow_cell = FlowCellDirectoryData(Path(flow_cell_directory_name_demultiplexed_with_bcl_convert))

    # THEN it sets the converter to BCLConverter
    assert flow_cell.bcl_converter == BclConverter.BCLCONVERT


def test_get_bcl_converter_bcl2fastq_flow_cell(
    flow_cell_directory_name_demultiplexed_with_bcl2fastq: str,
):
    """Test instantiating a flow cell with bcl2fastq as bcl converter."""
    # GIVEN a Bcl2Fastq flow cell directory

    # WHEN instantiating a flow cell object
    flow_cell = FlowCellDirectoryData(
        flow_cell_path=Path(flow_cell_directory_name_demultiplexed_with_bcl2fastq),
        bcl_converter=BclConverter.BCL2FASTQ,
    )

    # THEN it sets the converter to BCLConverter
    assert flow_cell.bcl_converter == BclConverter.BCL2FASTQ


@pytest.mark.parametrize(
    "flow_cell_fixture",
    [
        "hiseq_x_single_index_flow_cell",
        "hiseq_x_dual_index_flow_cell",
        "hiseq_2500_dual_index_flow_cell",
        "hiseq_2500_custom_index_flow_cell",
    ],
)
def test_run_parameters_path(flow_cell_fixture: str, request: FixtureRequest):
    """Test that the run parameters file is being fetched correctly for the HiSeq flow cells."""
    # GIVEN a flow cell with a run parameters
    flow_cell: FlowCellDirectoryData = request.getfixturevalue(flow_cell_fixture)

    # WHEN getting the run parameters file name
    run_parameters_path: Path = flow_cell.run_parameters_path

    # THEN it should exist and be the expected one
    assert run_parameters_path.exists()
    assert (
        run_parameters_path.name == DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE
        or run_parameters_path.name == DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE
    )


def test_run_parameters_path_when_non_existing(tmp_flow_cell_without_run_parameters_path: Path):
    """Test that getting the path of the run parameters path fails if the file does not exist."""
    # GIVEN a flowcell object with a directory without a run parameters file
    flow_cell = FlowCellDirectoryData(flow_cell_path=tmp_flow_cell_without_run_parameters_path)

    # WHEN fetching the run parameters path
    with pytest.raises(FlowCellError) as exc:
        # THEN a FlowCellError is raised
        flow_cell.run_parameters_path
    assert "No run parameters file found in flow cell" in str(exc.value)


@pytest.mark.parametrize(
    "flow_cell_fixture, expected_sequencer",
    [
        ("hiseq_2500_custom_index_flow_cell", Sequencers.HISEQGA),
        ("hiseq_x_single_index_flow_cell", Sequencers.HISEQX),
        ("novaseq_6000_post_1_5_kits_flow_cell", Sequencers.NOVASEQ),
        ("novaseq_x_flow_cell", Sequencers.NOVASEQX),
    ],
)
def test_flow_cell_run_parameters_type(
    flow_cell_fixture: str, expected_sequencer: str, request: FixtureRequest
):
    """Test that the run parameters of the flow cell is of the expected type."""
    # GIVEN a flow cell without _run_parameters
    flow_cell: FlowCellDirectoryData = request.getfixturevalue(flow_cell_fixture)
    assert not flow_cell._run_parameters

    # WHEN creating the run parameters of the flow cell
    run_parameters: RunParameters = flow_cell.run_parameters

    # THEN the run parameters sequencer is the same as of the flow cell
    assert run_parameters.sequencer == expected_sequencer


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
