from enum import StrEnum

from cg.constants import DataDelivery


class MetagenomeDeliveryType(StrEnum):
    FASTQ = DataDelivery.FASTQ
    NO_DELIVERY = DataDelivery.NO_DELIVERY
