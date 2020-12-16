"""Models used by hermes <-> cg interactions"""

from typing import List

from pydantic import BaseModel


class CGTag(BaseModel):
    """Specify the file output information from hermes"""

    path: str
    tags: List[str]


class CGDeliverables(BaseModel):
    """Class that specifies the output from hermes"""

    pipeline: str
    bundle_id: str
    files: List[CGTag]
