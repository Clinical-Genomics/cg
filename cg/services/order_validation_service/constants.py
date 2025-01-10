from enum import StrEnum, auto


class TissueBlockEnum(StrEnum):
    SMALL: str = auto()
    LARGE: str = auto()
    BLANK: str = ""


class ElutionBuffer(StrEnum):
    """The choices of buffers."""

    OTHER = "Other"
    TRIS_HCL = "Tris-HCl"
    WATER = "Nuclease-free water"


ALLOWED_SKIP_RC_BUFFERS = [ElutionBuffer.TRIS_HCL, ElutionBuffer.WATER]

MINIMUM_VOLUME, MAXIMUM_VOLUME = 20, 130


class ExtractionMethod(StrEnum):
    EZ1 = "EZ1"
    MAELSTROM = "Maelstrom"
    MAGNAPURE_96 = "MagNaPure 96"
    QIAGEN_MAGATTRACT = "Qiagen MagAttract"
    QIASYMPHONE = "QIAsymphony"
    OTHER = 'Other (specify in "Comments")'


class IndexEnum(StrEnum):
    IDT_DS_B = "IDT DupSeq 10 bp Set B"
    IDT_DS_F = "IDT DupSeq 10 bp Set F"
    DT_XGEN_UDI = "IDT xGen UDI Adapters"
    TRUSEQ_DNA_HT = "TruSeq DNA HT Dual-index (D7-D5)"
    NEXTFLEX_UDI_96 = "NEXTflex UDI Barcodes 1-96"
    NEXTFLEX_V2_UDI_96 = "NEXTflex v2 UDI Barcodes 1-96"
    NEXTERA_XT = "Nextera XT Dual"
    TWIST_UDI_A = "TWIST UDI Set A"
    TWIST_UDI_B = "TWIST UDI Set B"
    TWIST_UDI_C = "TWIST UDI Set C"
    TEN_X_TN_A = "10X Genomics Dual Index kit TN Set A"
    TEN_X_TT_A = "10X Genomics Dual Index kit TT Set A"
    KAPA_UDI_NIPT = "KAPA UDI NIPT"
    AVIDA_INDEX_PLATE = "Avida index plate"
    AVIDA_INDEX_STRIP = "Avida index strip"
    NOINDEX = "NoIndex"
