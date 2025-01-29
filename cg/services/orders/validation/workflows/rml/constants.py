from enum import StrEnum

from cg.constants.constants import DataDelivery


class RmlDeliveryType(StrEnum):
    FASTQ = DataDelivery.FASTQ
    NO_DELIVERY = DataDelivery.NO_DELIVERY
