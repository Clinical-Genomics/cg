from pathlib import Path

from cg.models.demultiplex.flowcell import Flowcell


def test_flowcell_id(flowcell_path: Path):
    # GIVEN the path to a finished flowcell run
    # GIVEN the flowcell id
    flowcell_id: str = flowcell_path.name.split("_")[-1][1:]

    # WHEN instantiating a flowcell object
    flowcell_obj = Flowcell(flowcell_path)

    # THEN assert that the flowcell flowcell id is correcly parsed
    assert flowcell_obj.flowcell_id == flowcell_id


def test_flowcell_position(flowcell_path: Path):
    # GIVEN the path to a finished flowcell
    # GIVEN a flowcell object
    flowcell_obj = Flowcell(flowcell_path)

    # WHEN fetching the flowcell position
    position = flowcell_obj.flowcell_position

    # THEN assert it is A or B
    assert position in ["A", "B"]


def test_rta_exists(flowcell_object: Flowcell):
    # GIVEN the path to a finished flowcell
    # GIVEN a flowcell object

    # WHEN fetching the path to the RTA file
    rta_file: Path = flowcell_object.rta_complete_path

    # THEN assert that the file exists
    assert rta_file.exists()
