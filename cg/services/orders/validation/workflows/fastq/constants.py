from enum import StrEnum

from cg.constants import DataDelivery


class FastqDeliveryType(StrEnum):
    FASTQ = DataDelivery.FASTQ
    NO_DELIVERY = DataDelivery.NO_DELIVERY
