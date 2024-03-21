from enum import IntEnum, StrEnum, auto


class Sex(StrEnum):
    FEMALE = auto()
    MALE = auto()
    UNKNOWN = auto()
    OTHER = auto()


class PhenotypeStatus(StrEnum):
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
