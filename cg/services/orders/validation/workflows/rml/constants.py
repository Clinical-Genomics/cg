from enum import StrEnum

from cg.constants.constants import DataDelivery


class RMLDeliveryType(StrEnum):
    FASTQ = DataDelivery.FASTQ
    NO_DELIVERY = DataDelivery.NO_DELIVERY
