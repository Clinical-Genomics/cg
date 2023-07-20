from datetime import date
from typing import Optional

from pydantic.v1 import BaseModel, conlist
from typing_extensions import Literal


class CrunchyFile(BaseModel):
    path: str
    file: Literal["first_read", "second_read", "spring"]
    checksum: Optional[str]
    algorithm: Literal["sha1", "md5", "sha256"] = None
    updated: date = None


class CrunchyMetadata(BaseModel):
    files: conlist(CrunchyFile, max_items=3, min_items=3)
