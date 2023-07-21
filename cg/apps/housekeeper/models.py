"""Housekeeper models"""
from datetime import datetime
from typing import List, Optional

from pydantic.v1 import BaseModel


class InputFile(BaseModel):
    path: str
    archive: bool = False
    tags: List[str]


class InputBundle(BaseModel):
    name: str
    created: datetime = datetime.now()
    expires: Optional[datetime]
    files: List[InputFile]
