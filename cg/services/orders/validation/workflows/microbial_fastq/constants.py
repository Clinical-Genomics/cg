from enum import StrEnum

from cg.constants import DataDelivery


class MicrobialFastqDeliveryType(StrEnum):
    FASTQ = DataDelivery.FASTQ
    NO_DELIVERY = DataDelivery.NO_DELIVERY
