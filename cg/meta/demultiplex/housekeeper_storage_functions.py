"""Functions interacting with housekeeper in the DemuxPostProcessingAPI."""

import logging
from pathlib import Path
from typing import Iterable

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.sequencing import Sequencers
from cg.meta.demultiplex.utils import (
    get_lane_from_sample_fastq,
    get_q30_threshold,
    get_sample_fastqs_from_flow_cell,
    get_sample_sheet_path_from_flow_cell_dir,
    get_undetermined_fastqs,
    rename_fastq_file_if_needed,
)
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.store.store import Store
from cg.utils.files import get_files_matching_pattern

LOG = logging.getLogger(__name__)


def store_flow_cell_data_in_housekeeper(
    flow_cell: IlluminaRunDirectoryData,
    hk_api: HousekeeperAPI,
    flow_cell_run_dir: Path,
    store: Store,
) -> None:
    LOG.info(f"Add flow cell data to Housekeeper for {flow_cell.id}")

    hk_api.add_bundle_and_version_if_non_existent(flow_cell.id)

    tags: list[str] = [SequencingFileTag.FASTQ, SequencingFileTag.RUN_PARAMETERS, flow_cell.id]
    hk_api.add_tags_if_non_existent(tags)

    add_sample_fastq_files_to_housekeeper(flow_cell=flow_cell, hk_api=hk_api, store=store)
    store_undetermined_fastq_files(flow_cell=flow_cell, hk_api=hk_api, store=store)
    add_demux_logs_to_housekeeper(
        flow_cell=flow_cell, hk_api=hk_api, flow_cell_run_dir=flow_cell_run_dir
    )
    add_run_parameters_file_to_housekeeper(
        flow_cell_name=flow_cell.full_name, flow_cell_run_dir=flow_cell_run_dir, hk_api=hk_api
    )


def store_undetermined_fastq_files(
    flow_cell: IlluminaRunDirectoryData, hk_api: HousekeeperAPI, store: Store
) -> None:
    """Store undetermined fastq files for non-pooled samples in Housekeeper."""
    non_pooled_lanes_and_samples: list[tuple[int, str]] = (
        flow_cell.sample_sheet.get_non_pooled_lanes_and_samples()
    )

    for lane, sample_id in non_pooled_lanes_and_samples:
        undetermined_fastqs: list[Path] = get_undetermined_fastqs(
            lane=lane, flow_cell_path=flow_cell.path
        )

        for fastq_path in undetermined_fastqs:
            if check_if_fastq_path_should_be_stored_in_housekeeper(
                sample_id=sample_id,
                sample_fastq_path=fastq_path,
                sequencer_type=flow_cell.sequencer_type,
                flow_cell_name=flow_cell.id,
                store=store,
            ):
                hk_api.store_fastq_path_in_housekeeper(
                    sample_internal_id=sample_id,
                    sample_fastq_path=fastq_path,
                    flow_cell_id=flow_cell.id,
                )


def add_demux_logs_to_housekeeper(
    flow_cell: IlluminaRunDirectoryData, hk_api: HousekeeperAPI, flow_cell_run_dir: Path
) -> None:
    """Add demux logs to Housekeeper."""
    log_file_name_pattern: str = r"*_demultiplex.std*"
    demux_log_file_paths: list[Path] = get_files_matching_pattern(
        directory=Path(flow_cell_run_dir, flow_cell.full_name), pattern=log_file_name_pattern
    )

    tag_names: list[str] = [SequencingFileTag.DEMUX_LOG, flow_cell.id]
    for log_file_path in demux_log_file_paths:
        try:
            hk_api.add_file_to_bundle_if_non_existent(
                file_path=log_file_path, bundle_name=flow_cell.id, tag_names=tag_names
            )
            LOG.info(f"Added demux log file {log_file_path} to Housekeeper.")
        except FileNotFoundError as e:
            LOG.error(f"Cannot find demux log file {log_file_path}. Error: {e}.")


def add_run_parameters_file_to_housekeeper(
    flow_cell_name: str, flow_cell_run_dir: Path, hk_api: HousekeeperAPI
) -> None:
    """Add run parameters file to Housekeeper."""
    flow_cell_path = Path(flow_cell_run_dir, flow_cell_name)
    flow_cell = IlluminaRunDirectoryData(flow_cell_path)
    run_parameters_file_path: Path = flow_cell.run_parameters_path
    tag_names: list[str] = [SequencingFileTag.RUN_PARAMETERS, flow_cell.id]
    hk_api.add_file_to_bundle_if_non_existent(
        file_path=run_parameters_file_path, bundle_name=flow_cell.id, tag_names=tag_names
    )
    LOG.info(
        f"Added run parameters file {run_parameters_file_path} to {flow_cell.id} in Housekeeper."
    )


def add_sample_fastq_files_to_housekeeper(
    flow_cell: IlluminaRunDirectoryData, hk_api: HousekeeperAPI, store: Store
) -> None:
    """Add sample fastq files from flow cell to Housekeeper."""
    sample_internal_ids: list[str] = flow_cell.sample_sheet.get_sample_ids()

    for sample_internal_id in sample_internal_ids:
        sample_fastq_paths: list[Path] | None = get_sample_fastqs_from_flow_cell(
            flow_cell_directory=flow_cell.path, sample_internal_id=sample_internal_id
        )

        if not sample_fastq_paths:
            LOG.warning(
                f"Cannot find fastq files for sample {sample_internal_id} in {flow_cell.path}. Skipping."
            )
            continue

        for sample_fastq_path in sample_fastq_paths:
            sample_fastq_path: Path = rename_fastq_file_if_needed(
                fastq_file_path=sample_fastq_path, flow_cell_name=flow_cell.id
            )
            if check_if_fastq_path_should_be_stored_in_housekeeper(
                sample_id=sample_internal_id,
                sample_fastq_path=sample_fastq_path,
                sequencer_type=flow_cell.sequencer_type,
                flow_cell_name=flow_cell.id,
                store=store,
            ):
                hk_api.store_fastq_path_in_housekeeper(
                    sample_internal_id=sample_internal_id,
                    sample_fastq_path=sample_fastq_path,
                    flow_cell_id=flow_cell.id,
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
        return metric.sample_base_percentage_passing_q30 >= q30_threshold

    LOG.warning(
        f"Skipping fastq file {sample_fastq_path.name} as no metrics entry was found in status db."
    )
    LOG.warning(f"Flow cell name: {flow_cell_name}, sample id: {sample_id}, lane: {lane} ")
    return False


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


def delete_sequencing_data_from_housekeeper(flow_cell_id: str, hk_api: HousekeeperAPI) -> None:
    """Delete FASTQ, SPRING and metadata files associated with a flow cell from Housekeeper."""
    tag_combinations: list[set[str]] = [
        {SequencingFileTag.FASTQ, flow_cell_id},
        {SequencingFileTag.SPRING, flow_cell_id},
        {SequencingFileTag.SPRING_METADATA, flow_cell_id},
    ]
    for tags in tag_combinations:
        housekeeper_files: Iterable[File] = hk_api.files(tags=tags)
        for housekeeper_file in housekeeper_files:
            hk_api.delete_file(file_id=housekeeper_file.id)
