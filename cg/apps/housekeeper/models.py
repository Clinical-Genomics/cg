"""Housekeeper models"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class InputFile(BaseModel):
    path: str
    archive: bool = False
    tags: List[str]


class InputBundle(BaseModel):
    name: str
    created: datetime = datetime.now()
    expires: Optional[datetime]
    files: List[InputFile]


if __name__ == "__main__":
    file_info = {"path": "tests/conftest.py", "tags": ["python", "testing"]}
    file_obj = InputFile(**file_info)
    print(file_obj)
    bundle_info = {"name": "bundle_name", "created": datetime.now(), "files": [file_info]}
    print(InputBundle(**bundle_info))
    bundle_info2 = {"name": "bundle_name", "created": None, "files": [file_info]}
    print(InputBundle(**bundle_info2))
