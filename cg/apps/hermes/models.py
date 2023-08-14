"""Models used by hermes <-> cg interactions"""
import logging
from pathlib import Path
from typing import List, Optional

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

    @field_validator("files", mode="before")
    def check_mandatory_exists(cls, file):
        if file.mandatory:
            assert Path(file.path).exists(), f"Mandatory file cannot be found at {file.path}"
            return file
        if not Path(file.path).exists():
            LOG.info("Optional file %s not found, removing from bundle", file.path)
            return
        return file

    @field_validator("files", mode="before")
    @classmethod
    def remove_invalid(cls, value):
        return [item for item in value if item]
