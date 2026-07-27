import configparser
from pathlib import Path

from pydantic import BaseModel


class RankModel(BaseModel):
    path: Path
    version: str


def parse_rank_model_file(file: Path) -> RankModel:
    """
    Parses a SNV or SV rank model file to extract its version given its path returning file path
    and version in a RankModel Pydantic object.
    It assumes that the rank model file is an INI file with a [Version] section and a version key.
    """
    config = configparser.ConfigParser()
    config.read(file)
    version: str | None = config.get("Version", "version", fallback=None)
    rank_model = RankModel(path=file, version=version)
    return rank_model
