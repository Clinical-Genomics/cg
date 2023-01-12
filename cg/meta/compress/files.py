"""Code to handle files regarding compression and decompression."""

import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from housekeeper.store.models import Version, File

from cg.constants import HK_FASTQ_TAGS, SequencingFileTag
from cg.constants.compression import (
    FASTQ_DATETIME_DELTA,
    FASTQ_FIRST_READ_SUFFIX,
    FASTQ_SECOND_READ_SUFFIX,
)
from cg.models import CompressionData
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)

# Functions to get common files


def get_hk_files_dict(tags: List[str], version_obj: Version) -> Dict[Path, File]:
    """Fetch files from a version in Housekeeper."""
    hk_file: Dict[Path, File] = {}
    tags: set = set(tags)
    for version_file in version_obj.files:
        file_tags: Set[str] = {tag.name for tag in version_file.tags}
        if not file_tags.intersection(tags):
            continue
        LOG.info(f"Found file {version_file.path}")
        path_obj: Path = Path(version_file.full_path)
        hk_file[path_obj] = version_file
    return hk_file


def is_file_in_version(version_obj: Version, path: Path) -> bool:
    """Check if a file is in a certain version."""
    return any(version_file.path == str(path) for version_file in version_obj.files)


# Functions to get FASTQ like files


def get_spring_paths(version_obj: Version) -> List[CompressionData]:
    """Get all SPRING paths for a sample."""
    hk_files_dict: Dict[Path, File] = get_hk_files_dict(
        tags=[SequencingFileTag.SPRING], version_obj=version_obj
    )
    spring_paths: list = []

    if hk_files_dict is None:
        return spring_paths

    spring_paths.extend(CompressionData(file_path.with_suffix("")) for file_path in hk_files_dict)
    return spring_paths


def get_fastq_stub(fastq_path: Path) -> Path:
    """Take a FASTQ file and return the stub (unique part).

    Example:
        fastq_file = /home/fastq_files/A_sequencing_run_R1_001.fastq.gz
        file_prefix = /home/fastq_files/A_sequencing_run
    """
    fastq_string: str = str(fastq_path)
    if FASTQ_FIRST_READ_SUFFIX in fastq_string:
        return Path(fastq_string.replace(FASTQ_FIRST_READ_SUFFIX, ""))
    if FASTQ_SECOND_READ_SUFFIX in fastq_string:
        return Path(fastq_string.replace(FASTQ_SECOND_READ_SUFFIX, ""))
    return None


def get_compression_data(fastq_files: List[Path]) -> List[CompressionData]:
    """Return a list of compression data objects.

    Each object has information about a pair of FASTQ files from the same run.
    """
    fastq_runs: set = set()
    compressions: List[CompressionData] = []
    for fastq_file in fastq_files:
        # file prefix is the run name identifier
        file_prefix: Optional[Path] = get_fastq_stub(fastq_file)
        if file_prefix is None:
            LOG.info(f"Invalid FASTQ name {fastq_file}")
            continue
        run_name: str = str(file_prefix)
        if run_name not in fastq_runs:
            fastq_runs.add(run_name)
            compressions.append(CompressionData(file_prefix))
    return compressions


def get_fastq_files(sample_id: str, version_obj: Version) -> Dict[str, dict]:
    """Get FASTQ files for sample."""
    hk_files_dict = get_hk_files_dict(tags=HK_FASTQ_TAGS, version_obj=version_obj)
    if hk_files_dict is None:
        return None

    fastq_dict = {}
    compression_objects: List[CompressionData] = get_compression_data(list(hk_files_dict.keys()))
    if not compression_objects:
        LOG.info(f"Could not find FASTQ files for {sample_id}")
        return None

    for compression_obj in compression_objects:

        if not check_fastqs(compression_obj):
            LOG.info(f"Skipping run {compression_obj.run_name}")
            continue
        fastq_dict[compression_obj.run_name] = {
            "compression_data": compression_obj,
            "hk_first": hk_files_dict[compression_obj.fastq_first],
            "hk_second": hk_files_dict[compression_obj.fastq_second],
        }

    return fastq_dict


def check_fastqs(compression_obj: CompressionData) -> bool:
    """Check if FASTQ files has the correct status.

    More specific this means to check
        - Did we get the full path of the file?
        - Does the file exist?
        - Do we have permissions?
        - Is the file actually a symlink?
        - Is the file a hardlink?
        - Is the file older than the specified time delta?
    """
    if not (
        compression_obj.is_absolute(compression_obj.fastq_first)
        or compression_obj.is_absolute(compression_obj.fastq_second)
    ):
        return False

    if not compression_obj.pair_exists():
        return False

    date_changed = compression_obj.get_change_date(compression_obj.fastq_first)
    today = datetime.datetime.now()

    # Check if date is older than FASTQ_DELTA
    if date_changed > today - FASTQ_DATETIME_DELTA:
        LOG.info("FASTQ files are not old enough")
        return False
    return True
