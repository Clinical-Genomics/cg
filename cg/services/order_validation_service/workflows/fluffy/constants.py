from enum import Enum

from cg.constants import DataDelivery


class fluffyDeliveryType(Enum):
    SCOUT = DataDelivery.SCOUT
    NO_DELIVERY = DataDelivery.NO_DELIVERY


class fluffyIndexEnum(Enum):
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
    NOINDEX = "NoIndex"
