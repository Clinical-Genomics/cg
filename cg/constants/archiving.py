from enum import StrEnum

DEFAULT_SPRING_ARCHIVE_COUNT = 100


class ArchiveLocations(StrEnum):
    """Archive locations for the different customers' Spring files."""

    KAROLINSKA_HOSPITAL: str = "KAROLINSKA_HOSPITAL"


PDC_ARCHIVE_LOCATION: str = "PDC"
