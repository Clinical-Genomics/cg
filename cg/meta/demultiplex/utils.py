import logging
import os
import re
from pathlib import Path

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.io.csv import read_csv, write_csv
from cg.utils.files import (
    get_file_in_directory,
    get_files_matching_pattern,
    is_pattern_in_file_path_name,
    rename_file,
)

LOG = logging.getLogger(__name__)

NANOPORE_SEQUENCING_SUMMARY_PATTERN: str = r"final_summary_*.txt"


def get_lane_from_sample_fastq(sample_fastq_path: Path) -> int:
    """
    Extract the lane number from the sample fastq path.
    Pre-condition:
        - The fastq file name contains the lane number formatted as _L<lane_number>
    """
    pattern = r"_L(\d+)"
    lane_match = re.search(pattern, sample_fastq_path.name)

    if lane_match:
        return int(lane_match.group(1))

    raise ValueError(f"Could not extract lane number from fastq file name {sample_fastq_path.name}")


def is_sample_id_in_directory_name(directory: Path, sample_internal_id: str) -> bool:
    """Validate that directory name is formatted as Sample_<sample_id> or Sample_<sample_id>_."""
    sample_pattern: str = f"Sample_{sample_internal_id}"
    return f"{sample_pattern}_" in directory.name or sample_pattern == directory.name


def is_sample_id_in_file_name(sample_fastq: Path, sample_internal_id: str) -> bool:
    """Validate that file name contains the sample id formatted as <sample_id>_."""
    return f"{sample_internal_id}_" in sample_fastq.name


def is_file_path_compressed_fastq(file_path: Path) -> bool:
    return file_path.name.endswith(f"{FileExtensions.FASTQ}{FileExtensions.GZIP}")


def is_lane_in_fastq_file_name(sample_fastq: Path) -> bool:
    """Validate that fastq contains lane number formatted as _L<lane_number>"""
    return bool(re.search(r"_L\d+", sample_fastq.name))


def is_valid_sample_fastq_file(sample_fastq: Path, sample_internal_id: str) -> bool:
    """
    Validate that the sample fastq file name is formatted as expected.

    Assumptions:
    1. The sample fastq file name ends with .fastq.gz
    2. The sample fastq file name contains the lane number formatted as _L<lane_number>
    3. The sample internal id is present in the parent directory name or in the file name.
    """
    sample_id_in_directory: bool = is_sample_id_in_directory_name(
        directory=sample_fastq.parent, sample_internal_id=sample_internal_id
    )
    sample_id_in_file_name: bool = is_sample_id_in_file_name(
        sample_fastq=sample_fastq, sample_internal_id=sample_internal_id
    )

    return (
        is_file_path_compressed_fastq(sample_fastq)
        and is_lane_in_fastq_file_name(sample_fastq)
        and (sample_id_in_directory or sample_id_in_file_name)
    )


def get_valid_sample_fastqs(fastq_paths: list[Path], sample_internal_id: str) -> list[Path]:
    """Return a list of valid fastq files."""
    return [
        fastq
        for fastq in fastq_paths
        if is_valid_sample_fastq_file(sample_fastq=fastq, sample_internal_id=sample_internal_id)
    ]


def get_sample_fastqs_from_flow_cell(
    flow_cell_directory: Path, sample_internal_id: str
) -> list[Path] | None:
    """Retrieve all fastq files for a specific sample in a flow cell directory."""

    # The flat output structure for NovaseqX flow cells demultiplexed with BCLConvert on hasta
    root_pattern = f"{sample_internal_id}_S*_L*_R*_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"

    # The pattern for novaseqx flow cells demultiplexed on board of the dragen
    demux_on_sequencer_pattern = (
        f"BCLConvert/fastq/{sample_internal_id}"
        f"_S*_L*_R*_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )

    for pattern in [
        root_pattern,
        demux_on_sequencer_pattern,
    ]:
        sample_fastqs: list[Path] = get_files_matching_pattern(
            directory=flow_cell_directory, pattern=pattern
        )
        valid_sample_fastqs: list[Path] = get_valid_sample_fastqs(
            fastq_paths=sample_fastqs, sample_internal_id=sample_internal_id
        )

        if valid_sample_fastqs:
            return valid_sample_fastqs


def create_delivery_file_in_flow_cell_directory(flow_cell_directory: Path) -> None:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()


def get_q30_threshold(sequencer_type: Sequencers) -> int:
    return FLOWCELL_Q30_THRESHOLD[sequencer_type]


def get_sample_sheet_path_from_flow_cell_dir(
    flow_cell_directory: Path,
    sample_sheet_file_name: str = DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME,
) -> Path:
    """Return the path to the sample sheet in the flow cell directory."""
    return get_file_in_directory(directory=flow_cell_directory, file_name=sample_sheet_file_name)


def add_flow_cell_name_to_fastq_file_path(fastq_file_path: Path, flow_cell_name: str) -> Path:
    """Add the flow cell name to the fastq file path if missing."""
    if is_pattern_in_file_path_name(file_path=fastq_file_path, pattern=flow_cell_name):
        LOG.debug(
            f"Flow cell name {flow_cell_name} already in {fastq_file_path}. Skipping renaming."
        )
        return fastq_file_path
    LOG.debug(f"Adding flow cell name {flow_cell_name} to {fastq_file_path}.")
    return Path(fastq_file_path.parent, f"{flow_cell_name}_{fastq_file_path.name}")


def rename_fastq_file_if_needed(fastq_file_path: Path, flow_cell_name: str) -> Path:
    """Rename the given fastq file path if the renamed fastq file path does not exist."""
    renamed_fastq_file_path: Path = add_flow_cell_name_to_fastq_file_path(
        fastq_file_path=fastq_file_path, flow_cell_name=flow_cell_name
    )
    if fastq_file_path != renamed_fastq_file_path:
        rename_file(file_path=fastq_file_path, renamed_file_path=renamed_fastq_file_path)
    return renamed_fastq_file_path


def get_undetermined_fastqs(lane: int, flow_cell_path: Path) -> list[Path]:
    """Get the undetermined fastq files for a specific lane on a flow cell."""
    undetermined_pattern = f"Undetermined*_L00{lane}_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    undetermined_in_root: list[Path] = get_files_matching_pattern(
        directory=flow_cell_path,
        pattern=undetermined_pattern,
    )
    return undetermined_in_root


def parse_manifest_file(manifest_file: Path) -> list[Path]:
    """Returns a list with the first entry of each row of the given TSV file."""
    LOG.debug(f"Parsing manifest file: {manifest_file}")
    files: list[list[str]] = read_csv(file_path=manifest_file, delimiter="\t")
    return [Path(file[0]) for file in files]


def is_file_relevant_for_demultiplexing(file: Path) -> bool:
    """Returns whether a file is relevant for demultiplexing."""
    relevant_directories = [DemultiplexingDirsAndFiles.INTER_OP, DemultiplexingDirsAndFiles.DATA]
    for relevant_directory in relevant_directories:
        if relevant_directory in file.parts:
            return True
    return False


def get_existing_manifest_file(source_directory: Path) -> Path | None:
    """Returns the first existing manifest file in the source directory."""
    manifest_file_paths = [
        Path(source_directory, DemultiplexingDirsAndFiles.ILLUMINA_FILE_MANIFEST),
        Path(source_directory, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST),
    ]
    for file_path in manifest_file_paths:
        if file_path.exists():
            return file_path


def are_all_files_synced(files_at_source: list[Path], target_directory: Path) -> bool:
    """Checks if all relevant files in the source are present in the target directory."""
    for file in files_at_source:
        target_file_path = Path(target_directory, file)
        if is_file_relevant_for_demultiplexing(file) and not target_file_path.exists():
            LOG.info(f"File: {file}, has not been transferred from source to {target_directory}")
            return False
    return True


def is_syncing_complete(source_directory: Path, target_directory: Path) -> bool:
    """Returns whether all relevant files for demultiplexing have been synced from the source to the target."""
    existing_manifest_file: Path | None = get_existing_manifest_file(source_directory)

    if not existing_manifest_file:
        LOG.debug(f"{source_directory} does not contain a manifest file. Skipping.")
        return False

    files_at_source: list[Path] = parse_manifest_file(existing_manifest_file)
    return are_all_files_synced(files_at_source=files_at_source, target_directory=target_directory)


def is_manifest_file_required(flow_cell_dir: Path) -> bool:
    """Returns whether a flow cell directory needs a manifest file."""
    illumina_manifest_file = Path(flow_cell_dir, DemultiplexingDirsAndFiles.ILLUMINA_FILE_MANIFEST)
    custom_manifest_file = Path(flow_cell_dir, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)
    copy_complete_file = Path(flow_cell_dir, DemultiplexingDirsAndFiles.COPY_COMPLETE)
    sequencing_finished: bool = copy_complete_file.exists() or is_nanopore_sequencing_complete(
        flow_cell_dir
    )
    return (
        not any((illumina_manifest_file.exists(), custom_manifest_file.exists()))
        and sequencing_finished
    )


def create_manifest_file(flow_cell_dir_name: Path) -> Path:
    """Creates a tab separated file containing the paths of all files in the given
    directory and any subdirectories."""
    files_in_directory: list[list[str]] = []
    for subdir, _, files in os.walk(flow_cell_dir_name):
        subdir = Path(subdir).relative_to(flow_cell_dir_name)
        files_in_directory.extend([Path(subdir, file).as_posix()] for file in files)
    LOG.info(
        f"Writing manifest file to {Path(flow_cell_dir_name, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)}"
    )
    output_path = Path(flow_cell_dir_name, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)
    write_csv(
        content=files_in_directory,
        file_path=output_path,
        delimiter="\t",
    )
    return output_path


def is_flow_cell_sync_confirmed(target_flow_cell_dir: Path) -> bool:
    return Path(target_flow_cell_dir, DemultiplexingDirsAndFiles.COPY_COMPLETE).exists()


def get_nanopore_summary_file(flow_cell_directory: Path) -> bool | None:
    """Returns the summary file for a Nanopore run if found."""
    try:
        file = Path(next(flow_cell_directory.glob(NANOPORE_SEQUENCING_SUMMARY_PATTERN)))
    except StopIteration:
        file = None
    return file


def is_nanopore_sequencing_complete(flow_cell_directory: Path) -> bool:
    """Returns whether the sequencing is complete for a Nanopore run."""
    return bool(get_nanopore_summary_file(flow_cell_directory))
