from enum import IntEnum, StrEnum


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"
    OTHER = "other"
    MISSING = ""


class PhenotypeStatus(StrEnum):
    UNKNOWN = "unknown"
    UNAFFECTED = "unaffected"
    AFFECTED = "affected"
    MISSING = ""


class PlinkPhenotypeStatus(IntEnum):
    UNKNOWN = 0
    UNAFFECTED = 1
    AFFECTED = 2


class PlinkSex(StrEnum):
    UNKNOWN = str(0)
    MALE = str(1)
    FEMALE = str(2)


class RelationshipStatus(StrEnum):
    HAS_NO_PARENT = str(0)
