from datetime import date

from pydantic import BaseModel, conlist
from typing_extensions import Literal


class CrunchyFile(BaseModel):
    path: str
    file: Literal["first_read", "second_read", "spring"]
    checksum: str | None = None
    algorithm: Literal["sha1", "md5", "sha256"] | None = None
    updated: date | None = None


class CrunchyMetadata(BaseModel):
    files: conlist(CrunchyFile, max_length=3, min_length=3)
