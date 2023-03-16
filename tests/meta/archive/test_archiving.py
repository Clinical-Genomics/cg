from pathlib import Path
from typing import Dict, List

from cg.meta.archive.ddn_dataflow import DDNDataFlowApi, TransferData


def test_correct_destination_root(
    ddn_api: DDNDataFlowApi, local_directory: str, transfer_data: TransferData
):
    """Tests the formatting function of the path dict for retrieving."""
    # GIVEN a source path and a destination path

    # WHEN creating the correctly formatted dictionary
    transfer_data.correct_destination_root()

    # THEN the destination path should be the local directory minus the /home part
    assert transfer_data.destination == (Path(*local_directory.parts[2:]))


def test_add_repositories(ddn_config, local_directory, remote_directory, transfer_data):
    transfer_data.add_repositories(
        source_prefix=ddn_config.local_storage, destination_prefix=ddn_config.archive_repository
    )
    assert transfer_data.source == ddn_config.local_storage + str(local_directory)


# TODO add more tests and clean them up
