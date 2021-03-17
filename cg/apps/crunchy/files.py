import json
import logging
import tempfile
from datetime import datetime
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Dict, List, Optional

from cg.utils.date import get_date
from cgmodels.crunchy.metadata import CrunchyFile, CrunchyMetadata

LOG = logging.getLogger(__name__)


# Methods to get file information
def get_log_dir(file_path: Path) -> Path:
    """Return the path to where logs should be stored"""
    return file_path.parent


def get_fastq_to_spring_sbatch_path(log_dir: Path, run_name: str = None) -> Path:
    """Return the path to where compression sbatch should be printed"""
    return log_dir / "_".join([run_name, "compress_fastq.sh"])


def get_spring_to_fastq_sbatch_path(log_dir: Path, run_name: str = None) -> Path:
    """Return the path to where decompression sbatch should be printed"""
    return log_dir / "_".join([run_name, "decompress_spring.sh"])


def get_tmp_dir(prefix: str, suffix: str, base: str = None) -> str:
    """Create a temporary directory and return the path to it"""

    with tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix, dir=base) as dir_name:
        tmp_dir_path = dir_name

    LOG.info("Created temporary dir %s", tmp_dir_path)
    return tmp_dir_path


def get_crunchy_metadata(metadata_path: Path) -> CrunchyMetadata:
    """Validate content of metadata file and return mapped content"""
    LOG.info("Fetch SPRING metadata from %s", metadata_path)
    with open(metadata_path, "r") as infile:
        try:
            content: List[Dict[str, str]] = json.load(infile)
        except JSONDecodeError:
            message = "No content in SPRING metadata file"
            LOG.warning(message)
            raise SyntaxError(message)
    metadata = CrunchyMetadata(files=content)

    if len(metadata.files) != 3:
        LOG.warning("Wrong number of files in SPRING metadata file: %s", metadata_path)
        LOG.info("Found %s files, should always be 3 files", len(metadata.files))
        raise SyntaxError

    return metadata


def get_file_updated_at(crunchy_metadata: CrunchyMetadata) -> Optional[datetime.date]:
    """Check if a SPRING metadata file has been updated and return the date when updated"""
    return crunchy_metadata.files[0].updated


def get_spring_archive_files(crunchy_metadata: CrunchyMetadata) -> Dict[str, CrunchyFile]:
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


def update_metadata_date(spring_metadata_path: Path) -> None:
    """Update date in the SPRING metadata file to today date"""

    now: datetime = get_date()
    spring_metadata: CrunchyMetadata = get_crunchy_metadata(spring_metadata_path)
    LOG.info("Adding today date to SPRING metadata file")
    for file_info in spring_metadata.files:
        file_info.updated = now.date()

    content: dict = json.loads(spring_metadata.json(exclude_none=True))
    with open(spring_metadata_path, "w") as outfile:
        outfile.write(json.dumps(content["files"]))
