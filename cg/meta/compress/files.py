"""Code to handle files regarding compression and decompression"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

from housekeeper.store import models as hk_models

from cg.apps.crunchy import CrunchyAPI
from cg.constants import (
    BAM_SUFFIX,
    FASTQ_FIRST_READ_SUFFIX,
    FASTQ_SECOND_READ_SUFFIX,
    HK_BAM_TAGS,
    HK_FASTQ_TAGS,
)

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
        LOG.debug("Found file %s", file_obj)
        path_obj = Path(file_obj.full_path)
        hk_files_dict[path_obj.resolve()] = file_obj
    return hk_files_dict


def get_nlinks(file_link: Path) -> int:
    """Get number of links to path"""
    return os.stat(file_link).st_nlink


# Functions to get bam like files


def get_bam_files(case_id: str, version_obj: hk_models.Version, scout_case: dict) -> dict:
    """
    Get bam-files that can be compressed for a case

    Returns:
        bam_dict (dict): for each sample in case, give file-object for .bam and .bai files

        {<sample_id>:
            {
                "bam": hk_models.File,
                "bam_path": Path,
                "bai": hk_models.File,
                "bai_path": Path,
            }
        }
    """

    hk_files_dict = get_hk_files_dict(tags=HK_BAM_TAGS, version_obj=version_obj)
    if not hk_files_dict:
        LOG.warning("No files found in latest housekeeper version for %s", case_id)
        return None
    LOG.debug("hk files dict found %s", hk_files_dict)

    hk_file_paths = set(hk_files_dict.keys())

    bam_dict = {}
    for sample in scout_case["individuals"]:
        sample_id = sample["individual_id"]
        LOG.info("Check bam file for sample %s in scout", sample_id)
        bam_file = sample.get("bam_file")

        bam_path = get_bam_path(bam_file, hk_file_paths)
        if not bam_path:
            continue

        bai_path = get_bam_index_path(bam_path, hk_file_paths)
        if not bai_path:
            continue

        bam_dict[sample_id] = {
            "bam": hk_files_dict[bam_path],
            "bam_path": bam_path,
            "bai": hk_files_dict[bai_path],
            "bai_path": bai_path,
        }

    return bam_dict


def get_bam_index_path(bam_path: Path, hk_files: set) -> Path:
    """Check if a bam has a index file and return it as a path"""

    # Check the index file
    bai_paths = CrunchyAPI.get_index_path(bam_path)
    bai_single_suffix = bai_paths["single_suffix"]
    bai_double_suffix = bai_paths["double_suffix"]

    if (bai_single_suffix not in hk_files) and (bai_double_suffix not in hk_files):
        LOG.warning("%s has no index-file", bam_path)
        return False

    bai_path = bai_single_suffix
    if bai_double_suffix.exists():
        bai_path = bai_double_suffix

    return bai_path


def get_bam_path(bam_file: str, hk_files: List[Path]) -> Path:
    """Take the path to a file in string format and return a path object

    The main purpose of this function is to check if the file is valid.
    """
    if not bam_file:
        LOG.warning("No bam file found")
        return None

    bam_path = Path(bam_file).resolve()
    # Check the bam file
    if bam_path.suffix != BAM_SUFFIX:
        LOG.warning("Alignment file does not have correct suffix %s", BAM_SUFFIX)
        return None

    if not bam_path.exists():
        LOG.warning("%s does not exist", bam_path)
        return None

    if bam_path not in hk_files:
        LOG.warning("%s not in latest version of housekeeper bundle", bam_path)
        return None

    if get_nlinks(bam_path) > 1:
        LOG.warning("%s has more than 1 links to same inode", bam_path)
        return None

    return bam_path


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
    """Remove the suffix of a fastq file and return the base name"""
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
        LOG.info("Could not find fastq files for %s", sample_id)
        return None

    for run in fastq_runs:

        sorted_fastqs = sort_fastqs(fastq_files=fastq_runs[run])
        if not sorted_fastqs:
            LOG.info("Could not sort FASTQ files for %s", sample_id)
        fastq_first = {"path": sorted_fastqs[0], "hk_file": hk_files_dict[sorted_fastqs[0]]}
        fastq_second = {"path": sorted_fastqs[1], "hk_file": hk_files_dict[sorted_fastqs[1]]}
        fastq_dict[run] = {
            "fastq_first_file": fastq_first,
            "fastq_second_file": fastq_second,
        }
    return fastq_dict


def sort_fastqs(fastq_files: List[Path]) -> Tuple[Path, Path]:
    """ Sort list of FASTQ files into correct read pair

    Check that the files exists and are correct

    Args:
        fastq_files(list(Path))

    Returns:
        sorted_fastqs(tuple): (fastq_first, fastq_second)
    """
    first_fastq = second_fastq = None
    for fastq_file in fastq_files:
        if not fastq_file.exists():
            LOG.info("%s does not exist", fastq_file)
            return None

        if get_nlinks(file_link=fastq_file) > 1:
            LOG.info("More than 1 inode to same file for %s", fastq_file)
            return None

        if str(fastq_file).endswith(FASTQ_FIRST_READ_SUFFIX):
            first_fastq = fastq_file
        if str(fastq_file).endswith(FASTQ_SECOND_READ_SUFFIX):
            second_fastq = fastq_file

    if not (first_fastq and second_fastq):
        LOG.warning("Could not find paired fastq files")
        return None

    if not check_prefixes(first_fastq, second_fastq):
        LOG.info("FASTQ files does not have matching prefix")
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
