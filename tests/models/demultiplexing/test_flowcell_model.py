from pathlib import Path

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.models.demultiplex.flow_cell import FlowCell


def test_flowcell_id(flow_cell_path: Path):
    """Test parsing of flow cell id."""
    # GIVEN the path to a finished flow cell run
    # GIVEN the flow cell id
    flowcell_id: str = flow_cell_path.name.split("_")[-1][1:]

    # WHEN instantiating a flow cell object
    flowcell_obj = FlowCell(flow_cell_path)

    # THEN assert that the flow cell id is parsed
    assert flowcell_obj.id == flowcell_id


def test_flowcell_position(flow_cell_path: Path):
    """Test getting flow cell position."""
    # GIVEN the path to a finished flow cell
    # GIVEN a flow cell object
    flowcell_obj = FlowCell(flow_cell_path)

    # WHEN fetching the flow cell position
    position = flowcell_obj.position

    # THEN assert it is A or B
    assert position in ["A", "B"]


def test_rta_exists(flow_cell: FlowCell):
    """Test return of RTS file."""
    # GIVEN the path to a finished flow cell
    # GIVEN a flow cell object

    # WHEN fetching the path to the RTA file
    rta_file: Path = flow_cell.rta_complete_path

    # THEN assert that the file exists
    assert rta_file.exists()


def test_is_hiseq_x_copy_completed_ready(flow_cell: FlowCell):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flow cell object
    # GIVEN a copy complete file

    # WHEN fetching the path to the copy complete file
    is_completed = flow_cell.is_hiseq_x_copy_completed()

    # THEN assert that the file exists
    assert is_completed is True


def test_is_hiseq_x_delivery_started_ready(flow_cell: FlowCell, demultiplexing_delivery_file: Path):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flow cell object
    # GIVEN a delivery file
    demultiplexing_delivery_file.touch()

    # WHEN checking the path to the delivery file
    is_delivered = flow_cell.is_hiseq_x_delivery_started()

    demultiplexing_delivery_file.unlink()

    # THEN assert that the file exists
    assert is_delivered is True


def test_is_hiseq_x_delivery_started_not_ready(flow_cell: FlowCell):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flow cell object

    # WHEN checking the path to the copy complete file
    is_delivered = flow_cell.is_hiseq_x_delivery_started()

    # THEN assert that the file do not exist
    assert is_delivered is False


def test_is_hiseq_x(flow_cell: FlowCell, hiseq_x_tile_dir: Path):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flow cell object
    # GIVEN a Hiseq X directory
    hiseq_x_tile_dir.mkdir(exist_ok=True)

    # WHEN checking the path to the Hiseq X flow cell directory
    is_hiseq_x = flow_cell.is_hiseq_x()

    # Clean up
    hiseq_x_tile_dir.rmdir()

    # THEN assert that the file exists
    assert is_hiseq_x is True
