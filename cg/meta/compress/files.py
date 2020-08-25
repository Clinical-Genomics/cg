"""Code to handle files regarding compression and decompression"""

import logging
from pathlib import Path
from typing import Dict, List

from housekeeper.store import models as hk_models

from cg.constants import (FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX,
                          HK_FASTQ_TAGS)
from cg.models import CompressionData

LOG = logging.getLogger(__name__)

# Functions to get common files


def get_hk_files_dict(
    tags: List[str], version_obj: hk_models.Version
) -> Dict[Path, hk_models.File]:
    """Fetch files from a version in HK

    Return a dict with Path object as keys and hk file objects as values
    """
    hk_files_dict = {}
    tags = set(tags)
    for file_obj in version_obj.files:
        file_tags = {tag.name for tag in file_obj.tags}
        if not file_tags.intersection(tags):
            continue
        LOG.info("Found file %s", file_obj.path)
        path_obj = Path(file_obj.full_path)
        hk_files_dict[path_obj] = file_obj
    return hk_files_dict


def is_file_in_version(version_obj: hk_models.Version, path: Path) -> bool:
    """Check if a file is in a certain version"""
    for file_obj in version_obj.files:
        if file_obj.path == str(path):
            return True
    return False


# Functions to get fastq like files


def get_spring_paths(version_obj: hk_models.Version) -> List[CompressionData]:
    """Get all spring paths for a sample"""
    hk_files_dict = get_hk_files_dict(tags=["spring"], version_obj=version_obj)
    spring_paths = []

    if hk_files_dict is None:
        return spring_paths

    for file_path in hk_files_dict:
        if file_path.suffix == ".spring":
            spring_paths.append(CompressionData(file_path.with_suffix("")))

    return spring_paths


def get_fastq_stub(fastq_path: Path) -> Path:
    """Take a fastq file and return the stub (unique part)

    Example:
        fastq_file = /home/fastq_files/A_sequencing_run_R1_001.fastq.gz
        stub = /home/fastq_files/A_sequencing_run
    """
    fastq_string = str(fastq_path)
    if FASTQ_FIRST_READ_SUFFIX in fastq_string:
        return Path(fastq_string.replace(FASTQ_FIRST_READ_SUFFIX, ""))
    if FASTQ_SECOND_READ_SUFFIX in fastq_string:
        return Path(fastq_string.replace(FASTQ_SECOND_READ_SUFFIX, ""))
    return None


def get_compression_data(fastq_files: List[Path]) -> List[CompressionData]:
    """Return a list of compression data objects

    Each object has information about a pair of fastq files from the same run
    """
    fastq_runs = set()
    compression_objects = []
    for fastq_file in fastq_files:
        # stub is the run name identifier
        stub = get_fastq_stub(fastq_file)
        if stub is None:
            LOG.info("Invalid fastq name %s", fastq_file)
            continue
        run_name = str(stub)
        if run_name not in fastq_runs:
            fastq_runs.add(run_name)
            compression_objects.append(CompressionData(stub))
    return compression_objects


def get_fastq_files(sample_id: str, version_obj: hk_models.Version) -> Dict[str, dict]:
    """Get FASTQ files for sample"""
    hk_files_dict = get_hk_files_dict(tags=HK_FASTQ_TAGS, version_obj=version_obj)
    if hk_files_dict is None:
        return None

    fastq_dict = {}
    compression_objects = get_compression_data(list(hk_files_dict.keys()))
    if not compression_objects:
        LOG.info("Could not find FASTQ files for %s", sample_id)
        return None

    for compression_obj in compression_objects:

        if not check_fastqs(compression_obj):
            LOG.info("Skipping run %s", compression_obj.run_name)
            continue
        fastq_dict[compression_obj.run_name] = {
            "compression_data": compression_obj,
            "hk_first": hk_files_dict[compression_obj.fastq_first],
            "hk_second": hk_files_dict[compression_obj.fastq_second],
        }

    return fastq_dict


def check_fastqs(compression_obj: CompressionData) -> bool:
    """Check if fastq files has the correct status

    More specific this means to check
        - Did we get the full path of the file?
        - Does the file exist?
        - Do we have permissions?
        - Is the file actually a symlink?
        - Is the file hardlinked?
    """
    if not (
        compression_obj.is_absolute(compression_obj.fastq_first)
        or compression_obj.is_absolute(compression_obj.fastq_first)
    ):
        return False

    if not compression_obj.pair_exists():
        return False

    # Check if file is hardlinked multiple times
    if (
        compression_obj.get_nlinks(compression_obj.fastq_first) > 1
        or compression_obj.get_nlinks(compression_obj.fastq_second) > 1
    ):
        LOG.info("More than 1 inode to same file for %s", compression_obj.run_name)
        return False

    # Check if the fastq file is a symlinc (soft link)
    if compression_obj.is_symlink(compression_obj.fastq_first) or compression_obj.is_symlink(
        compression_obj.fastq_second
    ):
        LOG.info("Run %s has symbolic link, skipping run", compression_obj.run_name)
        return False

    return True
