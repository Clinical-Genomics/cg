import logging
from pathlib import Path

from cg.utils.checksum.checksum import is_md5sum_correct

LOG = logging.getLogger(__name__)


def are_all_fastq_valid(fastq_paths: list[Path]) -> bool:
    """Return True if all fastq files of a given sample pass md5 checksum."""
    are_all_valid: bool = True
    for path in fastq_paths:
        if not is_md5sum_correct(path):
            are_all_valid = False
            LOG.warning(f"Sample {path} did not match the given md5sum")
    return are_all_valid
