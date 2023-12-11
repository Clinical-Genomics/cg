from pathlib import Path

from pydantic import BaseModel, field_validator


class FastqFileMeta(BaseModel):
    path: Path | None = None
    lane: int
    read_number: int
    undetermined: bool | None = None
    flow_cell_id: str

    @field_validator("lane", "read_number", mode="before")
    @classmethod
    def convert_to_int(cls, value: str) -> int:
        """Validate input as an int and return it."""
        if isinstance(value, str):
            return int(value)
        return value
