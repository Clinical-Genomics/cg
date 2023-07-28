"""Functions interacting with housekeeper in the DemuxPostProcessingAPI."""
import logging
from pathlib import Path
from typing import List, Optional
from housekeeper.store.models import Version
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.sequencing import Sequencers
from cg.store import Store
from cg.meta.demultiplex.utils import (
    get_lane_from_sample_fastq,
    get_q30_threshold,
    get_sample_fastqs_from_flow_cell,
    get_sample_sheet_path,
)
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_sample_internal_ids_from_sample_sheet,
)
from cg.utils.files import get_files_matching_pattern

LOG = logging.getLogger(__name__)


def store_flow_cell_data_in_housekeeper(
    flow_cell: FlowCellDirectoryData,
    hk_api: HousekeeperAPI,
    flow_cell_run_dir: Path,
    store: Store,
) -> None:
    LOG.info(f"Add flow cell data to Housekeeper for {flow_cell.id}")

    add_bundle_and_version_if_non_existent(bundle_name=flow_cell.id, hk_api=hk_api)

    tags: List[str] = [SequencingFileTag.FASTQ, SequencingFileTag.SAMPLE_SHEET, flow_cell.id]
    add_tags_if_non_existent(tag_names=tags, hk_api=hk_api)

    add_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell.path, flow_cell_name=flow_cell.id, hk_api=hk_api
    )
    add_sample_fastq_files_to_housekeeper(flow_cell=flow_cell, hk_api=hk_api, store=store)
    add_demux_logs_to_housekeeper(
        flow_cell=flow_cell, hk_api=hk_api, flow_cell_run_dir=flow_cell_run_dir
    )


def add_demux_logs_to_housekeeper(
    flow_cell: FlowCellDirectoryData, hk_api: HousekeeperAPI, flow_cell_run_dir: Path
) -> None:
    """Add demux logs to Housekeeper."""
    log_file_name_pattern: str = r"*_demultiplex.std*"
    demux_log_file_paths: List[Path] = get_files_matching_pattern(
        directory=Path(flow_cell_run_dir, flow_cell.full_name), pattern=log_file_name_pattern
    )

    tag_names: List[str] = [SequencingFileTag.DEMUX_LOG, flow_cell.id]
    for log_file_path in demux_log_file_paths:
        try:
            add_file_to_bundle_if_non_existent(
                file_path=log_file_path,
                bundle_name=flow_cell.id,
                tag_names=tag_names,
                hk_api=hk_api,
            )
            LOG.info(f"Added demux log file {log_file_path} to Housekeeper.")
        except FileNotFoundError as e:
            LOG.error(f"Cannot find demux log file {log_file_path}. Error: {e}.")


def add_sample_fastq_files_to_housekeeper(
    flow_cell: FlowCellDirectoryData, hk_api: HousekeeperAPI, store: Store
) -> None:
    """Add sample fastq files from flow cell to Housekeeper."""

    sample_internal_ids: List[str] = get_sample_internal_ids_from_sample_sheet(
        sample_sheet_path=flow_cell.sample_sheet_path,
        flow_cell_sample_type=flow_cell.sample_type,
    )

    for sample_internal_id in sample_internal_ids:
        sample_fastq_paths: Optional[List[Path]] = get_sample_fastqs_from_flow_cell(
            flow_cell_directory=flow_cell.path, sample_internal_id=sample_internal_id
        )

        if not sample_fastq_paths:
            LOG.warning(
                f"Cannot find fastq files for sample {sample_internal_id} in {flow_cell.path}. Skipping."
            )
            continue

        for sample_fastq_path in sample_fastq_paths:
            store_fastq_path_in_housekeeper(
                sample_internal_id=sample_internal_id,
                sample_fastq_path=sample_fastq_path,
                flow_cell=flow_cell,
                hk_api=hk_api,
                store=store,
            )


def store_fastq_path_in_housekeeper(
    sample_internal_id: str,
    sample_fastq_path: Path,
    flow_cell: FlowCellDirectoryData,
    hk_api: HousekeeperAPI,
    store: Store,
) -> None:
    sample_fastq_should_be_stored: bool = check_if_fastq_path_should_be_stored_in_housekeeper(
        sample_id=sample_internal_id,
        sample_fastq_path=sample_fastq_path,
        sequencer_type=flow_cell.sequencer_type,
        flow_cell_name=flow_cell.id,
        store=store,
    )

    if sample_fastq_should_be_stored:
        add_bundle_and_version_if_non_existent(bundle_name=sample_internal_id, hk_api=hk_api)
        add_file_to_bundle_if_non_existent(
            file_path=sample_fastq_path,
            bundle_name=sample_internal_id,
            tag_names=[SequencingFileTag.FASTQ, flow_cell.id],
            hk_api=hk_api,
        )


def check_if_fastq_path_should_be_stored_in_housekeeper(
    sample_id: str,
    sample_fastq_path: Path,
    sequencer_type: Sequencers,
    flow_cell_name: str,
    store: Store,
) -> bool:
    """
    Check if a sample fastq file should be tracked in Housekeeper.
    Only fastq files that pass the q30 threshold should be tracked.
    """
    lane = get_lane_from_sample_fastq(sample_fastq_path)
    q30_threshold: int = get_q30_threshold(sequencer_type)

    metric = store.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
        flow_cell_name=flow_cell_name,
        sample_internal_id=sample_id,
        lane=lane,
    )

    if metric:
        return metric.sample_base_fraction_passing_q30 >= q30_threshold / 100

    LOG.warning(
        f"Skipping fastq file {sample_fastq_path.name} as no metrics entry was found in status db."
    )
    LOG.warning(f"Flow cell name: {flow_cell_name}, sample id: {sample_id}, lane: {lane} ")
    return False


def add_sample_sheet_path_to_housekeeper(
    flow_cell_directory: Path, flow_cell_name: str, hk_api: HousekeeperAPI
) -> None:
    """Add sample sheet path to Housekeeper."""

    try:
        sample_sheet_file_path: Path = get_sample_sheet_path(
            flow_cell_directory=flow_cell_directory
        )

        add_file_to_bundle_if_non_existent(
            file_path=sample_sheet_file_path,
            bundle_name=flow_cell_name,
            tag_names=[SequencingFileTag.SAMPLE_SHEET, flow_cell_name],
            hk_api=hk_api,
        )
    except FileNotFoundError as e:
        LOG.error(
            f"Sample sheet for flow cell {flow_cell_name} in {flow_cell_directory} was not found, error: {e}"
        )


def add_bundle_and_version_if_non_existent(bundle_name: str, hk_api: HousekeeperAPI) -> None:
    """Add bundle if it does not exist."""
    if not hk_api.bundle(name=bundle_name):
        hk_api.create_new_bundle_and_version(name=bundle_name)


def add_tags_if_non_existent(tag_names: List[str], hk_api: HousekeeperAPI) -> None:
    """Ensure that tags exist in Housekeeper."""
    for tag_name in tag_names:
        if hk_api.get_tag(name=tag_name) is None:
            hk_api.add_tag(name=tag_name)


def add_file_to_bundle_if_non_existent(
    file_path: Path, bundle_name: str, tag_names: List[str], hk_api: HousekeeperAPI
) -> None:
    """Add file to Housekeeper if it has not already been added."""
    if not file_path.exists():
        LOG.warning(f"File does not exist: {file_path}")
        return

    if not file_exists_in_latest_version_for_bundle(
        file_path=file_path, bundle_name=bundle_name, hk_api=hk_api
    ):
        hk_api.add_and_include_file_to_latest_version(
            bundle_name=bundle_name,
            file=file_path,
            tags=tag_names,
        )


def file_exists_in_latest_version_for_bundle(
    file_path: Path, bundle_name: str, hk_api: HousekeeperAPI
) -> bool:
    """Check if file exists in latest version for bundle."""
    latest_version: Version = hk_api.get_latest_bundle_version(bundle_name=bundle_name)

    return any(
        file_path.name == Path(bundle_file.path).name for bundle_file in latest_version.files
    )
