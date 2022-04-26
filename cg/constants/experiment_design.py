from enum import Enum


class Container(str, Enum):
    TUBE = "tube"
    PLATE = "plate"


class Control(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
