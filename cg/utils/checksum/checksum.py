import hashlib
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)


def check_md5sum(file_path: Path, md5sum: str) -> bool:
    """Checks if the given md5_sum matches that of the given file"""
    BYTES_PER_CHUNK: int = 8192
    with open(file_path, "rb") as file:
        file_hash = hashlib.md5()
        chunk = file.read(BYTES_PER_CHUNK)
        while chunk:
            file_hash.update(chunk)
            chunk = file.read(BYTES_PER_CHUNK)
    calculated_md5sum = file_hash.hexdigest()
    if md5sum == calculated_md5sum:
        return True
    LOG.info("The given md5sum does not match the md5sum for file %s" % file_path)
    return False


def extract_md5sum(md5sum_file: Path) -> str:
    """Searches the first line of a file for a string matching the length of an md5sum"""
    with open(md5sum_file, "r") as md_file:
        first_line: str = md_file.readline()
    line_list = first_line.split(" ")
    for element in line_list:
        element = element.strip()
        if len(element) == 32 and "." not in element:
            md5sum = element
            return md5sum
    LOG.info("No valid md5sum found in file {}.".format(md5sum_file))
    return ""


def sha512_checksum(file: Path) -> str:
    """Generates the sha512 checksum of a file"""
    LOG.debug("Checksum for file %s: ", file)
    sha512_hash = hashlib.sha512()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha512_hash.update(chunk)
    LOG.debug("Result: %s", sha512_hash.hexdigest())
    return sha512_hash.hexdigest()
