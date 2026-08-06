import logging
import re
from datetime import date, datetime, timedelta
from json.decoder import JSONDecodeError
from math import ceil
from pathlib import Path

from cg.apps.crunchy.models import CrunchyFile, CrunchyMetadata
from cg.constants import FASTQ_DELTA
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, ReadStream, WriteFile
from cg.utils.date import get_date

LOG = logging.getLogger(__name__)

NR_OF_FILES_IN_METADATA = 3


# Methods to get file information
def get_log_dir(file_path: Path) -> Path:
    """Return the path to where logs should be stored"""
    return file_path.parent


def get_fastq_to_spring_sbatch_path(log_dir: Path, run_name: str = None) -> Path:
    """Return the path to where compression sbatch should be printed"""
    return Path(log_dir, "_".join([run_name, "compress_fastq.sh"]))


def get_spring_to_fastq_sbatch_path(log_dir: Path, run_name: str = None) -> Path:
    """Return the path to where decompression sbatch should be printed"""
    return Path(log_dir, "_".join([run_name, "decompress_spring.sh"]))


def get_tmp_dir(base: str) -> str:
    """Return a node-local temp dir path, unique per SLURM job.

    The path is expanded by the shell at job runtime (mkdir -p happens inside the
    generated sbatch script), so `base` never needs to exist on the submission host.
    """
    return f"{base.rstrip('/')}/${{SLURM_JOB_ID}}_spring"


FASTQ_RUN_NAME_PATTERN = re.compile(
    r"^(?P<flow_cell>[^_]+)_(?P<sample>[^_]+)_[^_]+_L(?P<lane>\d+)$"
)


def parse_run_name(run_name: str) -> tuple[str, str, int] | None:
    """Parse a FASTQ run stub into (flow_cell, sample_internal_id, lane).

    Expects the format {flow_cell}_{sample_internal_id}_{meta}_L{lane}, e.g.
    23MGTHLT4_AGG24568A8_S52_L004. Returns None if the run name doesn't match.
    """
    match: re.Match | None = FASTQ_RUN_NAME_PATTERN.match(run_name)
    if not match:
        return None
    return match["flow_cell"], match["sample"], int(match["lane"])


def scale_resource_by_reads(
    reads: int, slope: float, intercept: float, floor: int, cap: int
) -> int:
    """Linearly estimate a resource (e.g. GB or minutes) from reads: estimate = slope * reads + intercept.

    The estimate is rounded up and clamped to [floor, cap].
    """
    estimate: float = slope * reads + intercept
    return min(max(ceil(estimate), floor), cap)


def get_crunchy_metadata(metadata_path: Path) -> CrunchyMetadata:
    """Validate content of metadata file and return mapped content."""
    LOG.info(f"Fetch SPRING metadata from {metadata_path}")
    try:
        content: list[dict[str, str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.JSON, file_path=metadata_path
        )
    except JSONDecodeError:
        message = "No content in SPRING metadata file"
        LOG.warning(message)
        raise SyntaxError(message)
    metadata = CrunchyMetadata(files=content)

    if len(metadata.files) != NR_OF_FILES_IN_METADATA:
        LOG.warning(f"Wrong number of files in SPRING metadata file: {metadata_path}")
        LOG.info(
            f"Found {len(metadata.files)} files, should always be {NR_OF_FILES_IN_METADATA} files"
        )
        raise SyntaxError

    return metadata


def get_file_updated_at(crunchy_metadata: CrunchyMetadata) -> date | None:
    """Check if a SPRING metadata file has been updated and return the date when updated"""
    return crunchy_metadata.files[0].updated


def get_spring_archive_files(crunchy_metadata: CrunchyMetadata) -> dict[str, CrunchyFile]:
    """Map the files in SPRING metadata to a dictionary

    Returns: {
                "fastq_first" : {file_info},
                "fastq_second" : {file_info},
                "spring" : {file_info},
              }
    """
    names_map = {"first_read": "fastq_first", "second_read": "fastq_second", "spring": "spring"}
    archive_files = {}
    for file_info in crunchy_metadata.files:
        file_name = names_map[file_info.file]
        archive_files[file_name] = file_info
    return archive_files


def write_metadata_content(spring_metadata: CrunchyMetadata, spring_metadata_path: Path) -> None:
    """Update the file on disk."""
    content: dict = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=spring_metadata.json(exclude_none=True)
    )
    WriteFile.write_file_from_content(
        content=content["files"], file_format=FileFormat.JSON, file_path=spring_metadata_path
    )


def update_metadata_date(spring_metadata_path: Path) -> None:
    """Update date in the SPRING metadata file to today date"""
    now: datetime = get_date()
    spring_metadata: CrunchyMetadata = get_crunchy_metadata(spring_metadata_path)
    LOG.info("Adding today date to SPRING metadata file")
    for file_info in spring_metadata.files:
        file_info.updated = now.date()
    write_metadata_content(
        spring_metadata=spring_metadata, spring_metadata_path=spring_metadata_path
    )


def update_metadata_paths(spring_metadata_path: Path, new_parent_path: Path) -> None:
    """Update paths for file in SPRING metadata file."""
    spring_metadata: CrunchyMetadata = get_crunchy_metadata(metadata_path=spring_metadata_path)
    LOG.info(f"Updating file paths in SPRING metadata file: {spring_metadata_path}")
    for file in spring_metadata.files:
        file.path = Path(new_parent_path, Path(file.path).name)
    write_metadata_content(
        spring_metadata=spring_metadata, spring_metadata_path=spring_metadata_path
    )


def check_if_update_spring(file_date: date) -> bool:
    """Check if date is older than FASTQ_DELTA."""
    delta = file_date + timedelta(days=FASTQ_DELTA)
    now = datetime.now()
    if delta > now.date():
        LOG.info("FASTQ files are not old enough")
        return False
    return True
