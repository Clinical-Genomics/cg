import os
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


def test_is_prior_novaseq_copy_completed_ready(flowcell_object: Flowcell):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flowcell object
    # GIVEN a copy complete file

    # WHEN fetching the path to the copy complete file
    is_completed = flowcell_object.is_prior_novaseq_copy_completed()

    # THEN assert that the file exists
    assert is_completed is True


def test_is_prior_novaseq_delivery_started_ready(flowcell_object: Flowcell):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flowcell object
    # GIVEN a delivery file
    Path(flowcell_object.path, "delivery.txt").touch()

    # WHEN fetching the path to the copy complete file
    is_delivered = flowcell_object.is_prior_novaseq_delivery_started()

    os.remove(Path(flowcell_object.path, "delivery.txt").as_posix())

    # THEN assert that the file exists
    assert is_delivered is True


def test_is_prior_novaseq_delivery_started_not_ready(flowcell_object: Flowcell):
    # GIVEN the path to a demultiplexed finished flow cell
    # GIVEN a flowcell object

    # WHEN fetching the path to the copy complete file
    is_delivered = flowcell_object.is_prior_novaseq_delivery_started()

    # THEN assert that the file do not exist
    assert is_delivered is False
