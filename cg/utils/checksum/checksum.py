import hashlib
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)


def sha512_checksum(file: Path) -> str:
    """Generates the sha512 checksum of a file"""
    LOG.debug("Checksum for file %s: ", file)
    sha512_hash = hashlib.sha512()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha512_hash.update(chunk)
    LOG.debug("Result: %s", sha512_hash.hexdigest())
    return sha512_hash.hexdigest()
