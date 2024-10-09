import logging
from pathlib import Path
from typing import Iterable

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.sequencing import Sequencers
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.post_processing.utils import (
    is_sample_negative_control_with_reads_in_lane,
    get_lane_from_sample_fastq,
    get_q30_threshold,
    get_sample_fastqs_from_flow_cell,
    get_undetermined_fastqs,
    rename_fastq_file_if_needed,
)
from cg.store.models import Sample
from cg.store.store import Store
from cg.utils.files import get_files_matching_pattern

LOG = logging.getLogger(__name__)


def _should_fastq_path_be_stored_in_housekeeper(
    sample_id: str,
    sample_fastq_path: Path,
    sequencer_type: Sequencers,
    device_internal_id: str,
    store: Store,
) -> bool:
    """
    Check if a sample fastq file should be tracked in Housekeeper.
    Only fastq files that pass the q30 threshold should be tracked.
    """
    sample: Sample = store.get_sample_by_internal_id(internal_id=sample_id)

    lane = get_lane_from_sample_fastq(sample_fastq_path)
    q30_threshold: int = get_q30_threshold(sequencer_type)

    metric = store.get_illumina_metrics_entry_by_device_sample_and_lane(
        device_internal_id=device_internal_id,
        sample_internal_id=sample_id,
        lane=lane,
    )

    if metric:

        if is_sample_negative_control_with_reads_in_lane(
            is_negative_control=sample.is_negative_control, metric=metric
        ):
            return True

        return metric.base_passing_q30_percent >= q30_threshold

    LOG.warning(
        f"Skipping fastq file {sample_fastq_path.name} as no metrics entry was found in status db."
    )
    LOG.warning(f"Flow cell name: {device_internal_id}, sample id: {sample_id}, lane: {lane} ")
    return False


def add_sample_fastq_files_to_housekeeper(
    run_directory_data: IlluminaRunDirectoryData, hk_api: HousekeeperAPI, store: Store
) -> None:
    """Add sample fastq files from the demultiplex directory to Housekeeper."""
    sample_internal_ids: list[str] = run_directory_data.sample_sheet.get_sample_ids()
    for sample_internal_id in sample_internal_ids:
        sample_fastq_paths: list[Path] | None = get_sample_fastqs_from_flow_cell(
            demultiplexed_run_path=run_directory_data.get_demultiplexed_runs_dir(),
            sample_internal_id=sample_internal_id,
        )
        if not sample_fastq_paths:
            LOG.warning(
                f"Cannot find fastq files for sample {sample_internal_id} in "
                f"{run_directory_data.get_demultiplexed_runs_dir()}. Skipping."
            )
            continue
        for sample_fastq_path in sample_fastq_paths:
            sample_fastq_path: Path = rename_fastq_file_if_needed(
                fastq_file_path=sample_fastq_path, flow_cell_name=run_directory_data.id
            )
            if _should_fastq_path_be_stored_in_housekeeper(
                sample_id=sample_internal_id,
                sample_fastq_path=sample_fastq_path,
                sequencer_type=run_directory_data.sequencer_type,
                device_internal_id=run_directory_data.id,
                store=store,
            ):
                hk_api.create_bundle_and_add_file_with_tags(
                    bundle_name=sample_internal_id,
                    file_path=sample_fastq_path,
                    tags=[run_directory_data.id, sample_internal_id, SequencingFileTag.FASTQ],
                )


def store_undetermined_fastq_files(
    run_directory_data: IlluminaRunDirectoryData, hk_api: HousekeeperAPI, store: Store
) -> None:
    """Store undetermined fastq files for non-pooled samples in Housekeeper."""
    non_pooled_lanes_and_samples: list[tuple[int, str]] = (
        run_directory_data.sample_sheet.get_non_pooled_lanes_and_samples()
    )

    for lane, sample_id in non_pooled_lanes_and_samples:
        undetermined_fastqs: list[Path] = get_undetermined_fastqs(
            lane=lane, demultiplexed_run_path=run_directory_data.get_demultiplexed_runs_dir()
        )

        for fastq_path in undetermined_fastqs:
            if _should_fastq_path_be_stored_in_housekeeper(
                sample_id=sample_id,
                sample_fastq_path=fastq_path,
                sequencer_type=run_directory_data.sequencer_type,
                device_internal_id=run_directory_data.id,
                store=store,
            ):
                hk_api.create_bundle_and_add_file_with_tags(
                    bundle_name=sample_id,
                    file_path=fastq_path,
                    tags=[run_directory_data.id, SequencingFileTag.FASTQ, sample_id],
                )


def add_demux_logs_to_housekeeper(
    run_directory_data: IlluminaRunDirectoryData, hk_api: HousekeeperAPI
) -> None:
    """Add demux logs to Housekeeper."""
    log_file_name_pattern: str = r"*_demultiplex.std*"
    demux_log_file_paths: list[Path] = get_files_matching_pattern(
        directory=run_directory_data.get_sequencing_runs_dir(), pattern=log_file_name_pattern
    )

    tag_names: list[str] = [SequencingFileTag.DEMUX_LOG, run_directory_data.id]
    for log_file_path in demux_log_file_paths:
        try:
            hk_api.add_file_to_bundle_if_non_existent(
                file_path=log_file_path, bundle_name=run_directory_data.id, tag_names=tag_names
            )
            LOG.info(f"Added demux log file {log_file_path} to Housekeeper.")
        except FileNotFoundError as e:
            LOG.error(f"Cannot find demux log file {log_file_path}. Error: {e}.")


def add_run_parameters_file_to_housekeeper(
    run_directory_data: IlluminaRunDirectoryData, hk_api: HousekeeperAPI
) -> None:
    """Add run parameters file to Housekeeper."""
    run_parameters_file_path: Path = run_directory_data.run_parameters_path
    tag_names: list[str] = [SequencingFileTag.RUN_PARAMETERS, run_directory_data.id]
    hk_api.add_file_to_bundle_if_non_existent(
        file_path=run_parameters_file_path, bundle_name=run_directory_data.id, tag_names=tag_names
    )
    LOG.info(
        f"Added run parameters file {run_parameters_file_path} to {run_directory_data.id}"
        " in Housekeeper."
    )


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
