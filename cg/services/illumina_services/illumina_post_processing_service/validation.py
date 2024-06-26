import logging
from pathlib import Path

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import FlowCellError, MissingFilesError
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina_services.illumina_post_processing_service.utils import (
    get_sample_fastqs_from_flow_cell,
)

LOG = logging.getLogger(__name__)


def is_demultiplexing_complete(flow_cell_directory: Path) -> bool:
    return Path(flow_cell_directory, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()


def is_flow_cell_ready_for_delivery(flow_cell_directory: Path) -> bool:
    return Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).exists()


def validate_sample_sheet_exists(flow_cell: IlluminaRunDirectoryData) -> None:
    sample_sheet_path: Path = flow_cell.get_sample_sheet_path_hk()
    if not sample_sheet_path or not sample_sheet_path.exists():
        raise FlowCellError(f"Sample sheet {sample_sheet_path} does not exist in housekeeper.")
    LOG.debug(f"Found sample sheet {sample_sheet_path} in housekeeper.")


def validate_demultiplexing_complete(flow_cell_output_directory: Path) -> None:
    if not is_demultiplexing_complete(flow_cell_output_directory):
        raise FlowCellError(
            f"Demultiplexing not completed for flow cell directory {flow_cell_output_directory}."
        )


def validate_flow_cell_delivery_status(flow_cell_output_directory: Path, force: bool) -> None:
    if is_flow_cell_ready_for_delivery(flow_cell_output_directory) and not force:
        raise FlowCellError(
            f"Flow cell output directory {flow_cell_output_directory}"
            " has already been processed and is ready for delivery."
        )


def validate_flow_cell_has_fastq_files(flow_cell: IlluminaRunDirectoryData) -> None:
    """Check if any sample from the flow cell has fastq files.
    Raises: MissingFilesError
        When all samples have missing fastq files in the flow cell
    """
    sample_ids: list[str] = flow_cell.sample_sheet.get_sample_ids()
    for sample_id in sample_ids:
        fastq_files: list[Path] | None = get_sample_fastqs_from_flow_cell(
            demultiplexed_run_path=flow_cell.get_demultiplexed_runs_dir(),
            sample_internal_id=sample_id,
        )
        if fastq_files:
            LOG.debug(f"Flow cell {flow_cell.id} has at least one sample with fastq files")
            return
    raise MissingFilesError(
        f"No fastq files were found for any sample in flow cell {flow_cell.id} path: {flow_cell.path}"
    )


def is_flow_cell_ready_for_postprocessing(
    flow_cell_output_directory: Path,
    flow_cell: IlluminaRunDirectoryData,
    force: bool = False,
) -> None:
    validate_flow_cell_delivery_status(
        flow_cell_output_directory=flow_cell_output_directory, force=force
    )
    validate_sample_sheet_exists(flow_cell)
    validate_demultiplexing_complete(flow_cell_output_directory)
    validate_flow_cell_has_fastq_files(flow_cell)
