from enum import Enum, IntEnum, StrEnum


class Gender(StrEnum):
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

    def __str__(self) -> str:
        return str.__str__(self.value)


class RelationshipStatus(str, Enum):
    HAS_NO_PARENT = 0

    def __str__(self) -> str:
        return str.__str__(self.value)
