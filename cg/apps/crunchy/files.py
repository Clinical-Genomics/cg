import logging
import tempfile
from datetime import date, datetime
from json.decoder import JSONDecodeError
from pathlib import Path

from cg.apps.crunchy.models import CrunchyFile, CrunchyMetadata
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


def get_tmp_dir(prefix: str, suffix: str, base: str = None) -> str:
    """Create a temporary directory and return the path to it"""

    with tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix, dir=base) as dir_name:
        tmp_dir_path = dir_name

    LOG.info(f"Created temporary dir {tmp_dir_path}")
    return tmp_dir_path


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
