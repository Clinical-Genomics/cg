from enum import Enum

from cg.constants.constants import DataDelivery


class RmlDeliveryType(Enum):
    FASTQ = DataDelivery.FASTQ
    NO_DELIVERY = DataDelivery.NO_DELIVERY
