from enum import Enum, IntEnum, StrEnum, auto


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"
    OTHER = "other"
    MISSING = ""


class PhenotypeStatus(Enum):
    UNKNOWN = auto()
    UNAFFECTED = auto()
    AFFECTED = auto()


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
