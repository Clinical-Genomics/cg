import configparser

from pydantic import BaseModel


class RankModel(BaseModel):
    path: str
    version: str


def parse_rank_model_file(file: str) -> RankModel:
    """
    Parses a SNV or SV rank model file to extract its version given its path and returns the file
    path and version in a RankModel Pydantic object.
    It assumes that the rank model file is an INI file with a [Version] section and a version key.
    Other sections are irrelevant and could be duplicated.
    Raises:
        pydantic.ValidationError if the version is not found in the file
    """
    config = configparser.ConfigParser(strict=False)  # not strict to parse duplicated sections
    config.read(file)
    version: str | None = config.get("Version", "version", fallback=None)
    rank_model = RankModel(path=file, version=version)  # type: ignore
    return rank_model
