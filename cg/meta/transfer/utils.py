import logging
from pathlib import Path

from cg.utils.checksum.checksum import is_md5sum_correct

LOG = logging.getLogger(__name__)


def get_all_fastq_from_folder(sample_folder: Path) -> list[Path]:
    """Returns a list of all fastq.gz files in given folder."""
    all_fastqs: list[Path] = []
    for leaf in sample_folder.glob("*fastq.gz"):
        abs_path: Path = sample_folder.joinpath(leaf)
        LOG.info(f"Found file {str(abs_path)} inside folder {sample_folder}")
        all_fastqs.append(abs_path)
    return all_fastqs


def are_all_fastq_valid(fastq_paths: list[Path]) -> bool:
    """Return True if all fastq files of a given sample pass md5 checksum."""
    are_all_valid: bool = True
    for path in fastq_paths:
        if is_md5sum_correct(path):
            are_all_valid = False
            LOG.warning(f"Sample {path} did not match the given md5sum")
    return are_all_valid
