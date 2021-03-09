import json
import logging
from datetime import datetime
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Dict, List, Optional

from cg.utils.date import get_date_str
from cgmodels.crunchy.metadata import CrunchyFile, CrunchyMetadata
from pydantic import ValidationError

LOG = logging.getLogger(__name__)


def get_spring_metadata(metadata_path: Path) -> CrunchyMetadata:
    """Validate content of metadata file and return mapped content"""
    LOG.info("Fetch SPRING metadata from %s", metadata_path)
    with open(metadata_path, "r") as infile:
        try:
            content: List[Dict[str, str]] = json.load(infile)
        except JSONDecodeError:
            LOG.warning("No content in SPRING metadata file")
            raise SyntaxError
    try:
        metadata = CrunchyMetadata(files=content)
    except ValidationError:
        LOG.warning("Invalid spring metadata file %s", metadata_path)
        raise SyntaxError

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

    today_str = get_date_str()
    spring_metadata: CrunchyMetadata = get_spring_metadata(spring_metadata_path)
    LOG.info("Adding today date to SPRING metadata file")
    for file_info in spring_metadata.files:
        file_info.updated = today_str

    with open(spring_metadata_path, "w") as outfile:
        outfile.write(json.dumps(spring_metadata.json()))
