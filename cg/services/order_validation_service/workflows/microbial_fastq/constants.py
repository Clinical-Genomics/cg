from enum import Enum

from cg.constants import DataDelivery


class MicrobialFastqDeliveryType(Enum):
    FASTQ = DataDelivery.FASTQ
    NO_DELIVERY = DataDelivery.NO_DELIVERY
