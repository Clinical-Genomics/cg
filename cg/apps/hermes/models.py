"""Models used by hermes <-> cg interactions"""
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import AfterValidator, BaseModel
from typing_extensions import Annotated

LOG = logging.getLogger(__name__)


class CGTag(BaseModel):
    """Specify the file output information from hermes"""

    path: str
    tags: List[str]
    mandatory: Optional[bool] = False


def check_mandatory_exists(file: CGTag) -> Optional[CGTag]:
    if file.mandatory:
        assert Path(file.path).exists(), f"Mandatory file cannot be found at {file.path}"
        return file
    if not Path(file.path).exists():
        LOG.info(f"Optional file {file.path} not found, removing from bundle")
        return
    return file


def remove_invalid(files: List[Optional[CGTag]]) -> List[CGTag]:
    return [file for file in files if file]

class CGDeliverables(BaseModel):
    """Class that specifies the output from hermes"""

    pipeline: str
    bundle_id: str
    files: List[Annotated[CGTag, AfterValidator(check_mandatory_exists), AfterValidator(remove_invalid)]]
