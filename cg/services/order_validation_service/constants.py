from enum import Enum, StrEnum, auto


class TissueBlockEnum(StrEnum):
    SMALL: str = auto()
    LARGE: str = auto()
    BLANK: str = ""


class ElutionBuffer(StrEnum):
    """The choices of buffers."""

    OTHER = 'Other (specify in "Comments")'
    TRIS_HCL = "Tris-HCl"
    WATER = "Nuclease-free water"


ALLOWED_SKIP_RC_BUFFERS = ["Nuclease-free water", "Tris-HCl"]

MINIMUM_VOLUME, MAXIMUM_VOLUME = 20, 130


class ExtractionMethod(Enum):
    EZ1 = "EZ1"
    MAELSTROM = "Maelstrom"
    MAGNAPURE_96 = "MagNaPure 96 (contact Clinical Genomics before submission)"
    QIAGEN_MAGATTRACT = "Qiagen MagAttract"
    QIASYMPHONE = "QIAsymphony"
    OTHER = 'Other (specify in "Comments")'
