from enum import StrEnum

from cg.constants import DataDelivery


class PacbioDeliveryType(StrEnum):
    BAM = DataDelivery.BAM
    NO_DELIVERY = DataDelivery.NO_DELIVERY
