from enum import Enum, IntEnum


class Gender(str, Enum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"
    OTHER = "other"
    MISSING = None

    def __repr__(self):
        return self.value


class PhenotypeStatus(str, Enum):
    UNKNOWN = "unknown"
    UNAFFECTED = "unaffected"
    AFFECTED = "affected"
    MISSING = None

    def __repr__(self):
        return self.value


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
