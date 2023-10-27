from enum import StrEnum, IntEnum


class Gender(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"
    OTHER = "other"
    MISSING = ""

    def __repr__(self):
        return self.value


class PhenotypeStatus(StrEnum):
    UNKNOWN = "unknown"
    UNAFFECTED = "unaffected"
    AFFECTED = "affected"
    MISSING = ""

    def __repr__(self):
        return self.value


class PlinkPhenotypeStatus(IntEnum):
    UNKNOWN = 0
    UNAFFECTED = 1
    AFFECTED = 2


class PlinkGender(StrEnum):
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2


class RelationshipStatus(StrEnum):
    HAS_NO_PARENT = 0
