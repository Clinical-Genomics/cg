"""Utils for sample sheet generation."""

import logging
from pathlib import Path
from housekeeper.store.models import File
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.utils.files import get_file_in_directory

LOG = logging.getLogger(__name__)


def add_and_include_sample_sheet_path_to_housekeeper(
    flow_cell_directory: Path, flow_cell_name: str, hk_api: HousekeeperAPI
) -> None:
    """
    Add sample sheet path to Housekeeper.
    Raises:
        FileNotFoundError: If the sample sheet file is not found.
    """
    LOG.debug("Adding sample sheet to Housekeeper")
    try:
        sample_sheet_file_path: Path = get_sample_sheet_path_from_flow_cell_dir(flow_cell_directory)
        hk_api.add_bundle_and_version_if_non_existent(flow_cell_name)
        hk_api.add_file_to_bundle_if_non_existent(
            file_path=sample_sheet_file_path,
            bundle_name=flow_cell_name,
            tag_names=[SequencingFileTag.SAMPLE_SHEET, flow_cell_name],
        )
    except FileNotFoundError as e:
        LOG.error(
            f"Sample sheet for flow cell {flow_cell_name} in {flow_cell_directory} was not found, error: {e}"
        )


def delete_sample_sheet_from_housekeeper(flow_cell_id: str, hk_api: HousekeeperAPI) -> None:
    """Delete a sample sheet from Housekeeper database and disk given its path."""
    sample_sheet_file_path: Path = hk_api.get_sample_sheet_path(flow_cell_id)
    file: File = hk_api.get_file_insensitive_path(sample_sheet_file_path)
    hk_api.delete_file(file_id=file.id)


def get_sample_sheet_path_from_flow_cell_dir(
    flow_cell_directory: Path,
    sample_sheet_file_name: str = DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME,
) -> Path:
    """Return the path to the sample sheet in the flow cell directory."""
    return get_file_in_directory(directory=flow_cell_directory, file_name=sample_sheet_file_name)
