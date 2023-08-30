"""Models used by hermes <-> cg interactions"""
import logging
from pathlib import Path
from typing import List, Optional

from cg.exc import CgDataError
from pydantic import BaseModel, field_validator

LOG = logging.getLogger(__name__)


class CGTag(BaseModel):
    """Specify the file output information from hermes"""

    path: str
    tags: List[str]
    mandatory: Optional[bool] = False


class CGDeliverables(BaseModel):
    """Class that specifies the output from hermes"""

    pipeline: str
    bundle_id: str
    files: List[CGTag]

    @classmethod
    @field_validator("files")
    def remove_missing_files(cls, files: List[CGTag]) -> List[CGTag]:
        """Validates that the files in a suggested CGDeliverables object are correct.
        I.e. if a file doesn't exist an error is raised if the file was mandatory,
        otherwise it is simply removed from the list of files."""
        filtered_files: List[CGTag] = files.copy()
        for file in files:
            if file.mandatory and not Path(file.path).exists():
                raise CgDataError(f"Mandatory file cannot be found at {file.path}")
            if not Path(file.path).exists():
                LOG.info(f"Optional file {file.path} not found, removing from bundle.")
                filtered_files.remove(file)
        return filtered_files
