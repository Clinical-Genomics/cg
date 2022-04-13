from enum import Enum


class Gender(str, Enum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"
    OTHER = "other"


class PlinkGender(str, Enum):
    FEMALE = 2
    MALE = 1
    UNKNOWN = 0
