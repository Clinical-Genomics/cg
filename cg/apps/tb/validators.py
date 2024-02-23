import datetime as dt
from pathlib import Path

from dateutil.parser import parse as parse_datestr


def parse_str_to_datetime(value: str) -> dt.datetime | None:
    if value:
        return parse_datestr(value)


def parse_str_to_path(value: str) -> Path | None:
    if value:
        return Path(value)
