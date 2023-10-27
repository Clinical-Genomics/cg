from enum import StrEnum


class ArchiveLocations(StrEnum):
    """Demultiplexing related directories and files."""

    KAROLINSKA_BUCKET: str = "karolinska_bucket"
