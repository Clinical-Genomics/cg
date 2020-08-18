"""Code to handle files regarding compression and decompression"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

from housekeeper.store import models as hk_models

from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX, HK_FASTQ_TAGS

LOG = logging.getLogger(__name__)

# Functions to get common files


def get_hk_files_dict(tags: List[str], version_obj: hk_models.Version) -> dict:
    """Fetch files from a version in HK
        Return a dict with Path object as keys and hk file objects as values

    Returns:
        {
            Path(file): hk.File(file)
        }

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


def get_nlinks(file_link: Path) -> int:
    """Get number of links to path"""
    return os.stat(file_link).st_nlink


# Functions to get fastq like files


def get_spring_paths(version_obj: hk_models.Version) -> List[Path]:
    """Get all spring paths for a sample"""
    hk_files_dict = get_hk_files_dict(tags=["spring"], version_obj=version_obj)
    if hk_files_dict is None:
        return None

    spring_paths = []
    for file_path in hk_files_dict:
        if file_path.suffix == ".spring":
            spring_paths.append(file_path)

    return spring_paths


def get_run_name(fastq_path: Path) -> str:
    """Remove the suffix of a fastq file and return the sequencing run base name"""
    if not is_valid_fastq_suffix(fastq_path):
        return None

    if str(fastq_path).endswith(FASTQ_FIRST_READ_SUFFIX):
        return fastq_path.name.replace(FASTQ_FIRST_READ_SUFFIX, "")
    return fastq_path.name.replace(FASTQ_SECOND_READ_SUFFIX, "")


def get_fastq_runs(fastq_files: List[Path]) -> Dict[str, list]:
    """Return a dictionary with all individual runs and the files belonging to that run as values"""
    fastq_runs = {}
    for fastq_file in fastq_files:
        run_name = get_run_name(fastq_file)
        if not run_name:
            continue
        if run_name not in fastq_runs:
            LOG.info("Found run %s", run_name)
            fastq_runs[run_name] = []
        fastq_runs[run_name].append(fastq_file)

    return fastq_runs


def get_fastq_files(sample_id: str, version_obj: hk_models.Version) -> Dict[str, dict]:
    """Get FASTQ files for sample"""
    hk_files_dict = get_hk_files_dict(tags=HK_FASTQ_TAGS, version_obj=version_obj)
    if hk_files_dict is None:
        return None

    fastq_dict = {}
    fastq_runs = get_fastq_runs(list(hk_files_dict.keys()))
    if not fastq_runs:
        LOG.info("Could not find FASTQ files for %s", sample_id)
        return None

    for run in fastq_runs:

        sorted_fastqs = sort_fastqs(fastq_files=fastq_runs[run])
        if not sorted_fastqs:
            LOG.info("Skipping run %s", run)
            continue

        fastq_first = {"path": sorted_fastqs[0], "hk_file": hk_files_dict[sorted_fastqs[0]]}
        fastq_second = {"path": sorted_fastqs[1], "hk_file": hk_files_dict[sorted_fastqs[1]]}
        fastq_dict[run] = {
            "fastq_first_file": fastq_first,
            "fastq_second_file": fastq_second,
        }

    return fastq_dict


def check_file_status(file_path: Path) -> bool:
    """Check if a file has the correct status

    More specific this means to check
        - Did we get the full path of the file?
        - Does the file exist?
        - Do we have permissions?
        - Is the file actually a symlink?
        - Is the file hardlinked?
    """
    if not file_path.is_absolute():
        LOG.info("Could not resolve full path from HK to %s", file_path)
        return False

    try:
        if not file_path.exists():
            LOG.info("%s does not exist", file_path)
            return False
    except PermissionError:
        LOG.warning("Not permitted to access %s. Skipping", file_path)
        return False

    # Check if file is hardlinked multiple times
    if get_nlinks(file_link=file_path) > 1:
        LOG.info("More than 1 inode to same file for %s", file_path)
        return False

    # Check if the fastq file is a symlinc (soft link)
    if file_path.is_symlink():
        LOG.info("File %s is a symbolic link, skipping file", file_path)
        return False

    return True


def sort_fastqs(fastq_files: List[Path]) -> Tuple[Path, Path]:
    """ Sort list of FASTQ files into correct read pair

    Check that the files exists and are correct

    More specific we will do the following checks, if one is failing we skip the files:

        1. Does the file exist?
        2. Do we have permission to read the file?
        3. Are there more than one inode to the file (hardlinked)
        4. Is the file actually a soft link?
        5. Are there two correct files in the pair?
        6. Do they have the same prefix?

    Args:
        fastq_files(list(Path))

    Returns:
        sorted_fastqs(tuple): (fastq_first, fastq_second)
    """
    first_fastq = second_fastq = None
    for fastq_file in fastq_files:

        if not check_file_status(fastq_file):
            return None

        if str(fastq_file).endswith(FASTQ_FIRST_READ_SUFFIX):
            first_fastq = fastq_file
        if str(fastq_file).endswith(FASTQ_SECOND_READ_SUFFIX):
            second_fastq = fastq_file

    if not (first_fastq and second_fastq):
        LOG.warning("Could not find paired fastq files")
        return None

    if not check_prefixes(first_fastq, second_fastq):
        LOG.info("FASTQ files does not have matching prefix: %s, %s", first_fastq, second_fastq)
        return None

    return (first_fastq, second_fastq)


def check_prefixes(first_fastq: Path, second_fastq: Path) -> bool:
    """Check if two files belong to the same read pair"""
    first_prefix = str(first_fastq.absolute()).replace(FASTQ_FIRST_READ_SUFFIX, "")
    second_prefix = str(second_fastq.absolute()).replace(FASTQ_SECOND_READ_SUFFIX, "")
    return first_prefix == second_prefix


def is_valid_fastq_suffix(fastq_path: Path) -> bool:
    """ Check that fastq has correct suffix"""
    if str(fastq_path).endswith(FASTQ_FIRST_READ_SUFFIX) or str(fastq_path).endswith(
        FASTQ_SECOND_READ_SUFFIX
    ):
        return True
    return False


# Functions to check for files in housekeeper


def is_file_in_version(version_obj: hk_models.Version, path: Path) -> bool:
    """Check if a file is in a certain version"""
    for file_obj in version_obj.files:
        if file_obj.path == str(path):
            return True
    return False
