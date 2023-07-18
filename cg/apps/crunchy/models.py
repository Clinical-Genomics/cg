from datetime import date
from typing import List, Optional

from pydantic import Field, BaseModel
from typing_extensions import Annotated, Literal


class CrunchyFile(BaseModel):
    path: str
    file: Literal["first_read", "second_read", "spring"]
    checksum: Optional[str] = None
    algorithm: Literal["sha1", "md5", "sha256"] = None
    updated: date = None


class CrunchyMetadata(BaseModel):
    files: Annotated[List[CrunchyFile], Field(max_length=3, min_length=3)]
