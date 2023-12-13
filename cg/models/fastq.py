from pathlib import Path
from typing import Callable

from pydantic import BaseModel


class FastqFileMeta(BaseModel):
    path: Path | None = None
    lane: int
    read_direction: int
    undetermined: bool | None = None
    flow_cell_id: str


def _get_header_meta_casava_five_parts(parts: list[str]) -> FastqFileMeta:
    return FastqFileMeta(
        lane=parts[1], flow_cell_id="XXXXXX", read_direction=parts[-1].split("/")[-1]
    )


def _get_header_meta_casava_ten_parts(parts: list[str]) -> FastqFileMeta:
    return FastqFileMeta(
        lane=parts[3], flow_cell_id=parts[2], read_direction=parts[6].split(" ")[-1]
    )


def _get_header_meta_casava_seven_parts(parts: list[str]) -> FastqFileMeta:
    return FastqFileMeta(
        lane=parts[3], flow_cell_id=parts[2], read_direction=parts[-1].split("/")[-1]
    )


class GetFastqFileMeta:
    header_format: dict[int, Callable] = {
        5: _get_header_meta_casava_five_parts,
        7: _get_header_meta_casava_seven_parts,
        10: _get_header_meta_casava_ten_parts,
    }
