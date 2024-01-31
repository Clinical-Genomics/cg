"""Housekeeper models"""

from datetime import datetime

from pydantic import BaseModel


class InputFile(BaseModel):
    path: str
    archive: bool = False
    tags: list[str]


class InputBundle(BaseModel):
    name: str
    created: datetime = datetime.now()
    expires: datetime | None = None
    files: list[InputFile]
