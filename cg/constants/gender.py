from enum import Enum


class Gender(str, Enum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"
