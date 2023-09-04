from datetime import date
from typing import Optional

from pydantic import BaseModel, conlist
from typing_extensions import Literal


class CrunchyFile(BaseModel):
    path: str
    file: Literal["first_read", "second_read", "spring"]
    checksum: Optional[str] = None
    algorithm: Optional[Literal["sha1", "md5", "sha256"]] = None
    updated: Optional[date] = None


class CrunchyMetadata(BaseModel):
    files: conlist(CrunchyFile, max_length=3, min_length=3)
