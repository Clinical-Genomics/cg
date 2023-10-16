"""Housekeeper models"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InputFile(BaseModel):
    path: str
    archive: bool = False
    tags: list[str]


class InputBundle(BaseModel):
    name: str
    created: datetime = datetime.now()
    expires: Optional[datetime] = None
    files: list[InputFile]
