"""Models used by hermes <-> cg interactions"""

import logging
from pathlib import Path

from pydantic import BaseModel, field_validator

from cg.exc import CgDataError

LOG = logging.getLogger(__name__)


class CGTag(BaseModel):
    """Specify the file output information from hermes"""

    path: str
    tags: list[str]
    mandatory: bool | None = False


class CGDeliverables(BaseModel):
    """Class that specifies the output from Hermes."""

    workflow: str
    bundle_id: str
    files: list[CGTag]

    @field_validator("files")
    @classmethod
    def remove_missing_files(cls, files: list[CGTag]) -> list[CGTag]:
        """Validates that the files in a suggested CGDeliverables object are correct.
        I.e., if a file doesn't exist, an error is raised if the file was mandatory,
        otherwise it is simply removed from the list of files."""
        filtered_files: list[CGTag] = files.copy()
        for file in files:
            if file.mandatory and not Path(file.path).exists():
                raise CgDataError(f"Mandatory file cannot be found at {file.path}")
            if not Path(file.path).exists():
                LOG.info(f"Optional file {file.path} not found, removing from bundle.")
                filtered_files.remove(file)
        return filtered_files
