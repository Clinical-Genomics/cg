from enum import Enum, IntEnum


class Gender(str, Enum):
    FEMALE = "female"
    MALE = "male"
    OTHER = "other"
    UNKNOWN = "unknown"
    MISSING = None


class PhenotypeStatus(str, Enum):
    UNKNOWN = "unknown"
    UNAFFECTED = "unaffected"
    AFFECTED = "affected"
    MISSING = None


class PlinkPhenotypeStatus(IntEnum):
    UNKNOWN = 0
    UNAFFECTED = 1
    AFFECTED = 2


class PlinkGender(str, Enum):
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2


class RelationshipStatus(str, Enum):
    HAS_NO_PARENT = 0
