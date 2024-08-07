from enum import StrEnum

DEFAULT_SPRING_ARCHIVE_COUNT = 300


class ArchiveLocations(StrEnum):
    """Archive locations for the different customers' Spring files."""

    KAROLINSKA_BUCKET: str = "karolinska_bucket"


PDC_ARCHIVE_LOCATION: str = "PDC"
