import datetime as dt
from pathlib import Path
from typing import Dict, Optional

from dateutil.parser import parse as parse_datestr


def parse_str_to_datetime(value: str) -> Optional[dt.datetime]:
    if value:
        return parse_datestr(value)


def inherit_family_value(value: str, values: Dict) -> Optional[str]:
    return values.get("family")


def parse_str_to_path(value: str) -> Optional[Path]:
    if value:
        return Path(value)
