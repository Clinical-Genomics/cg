from enum import StrEnum

from cg.constants import DataDelivery


class FluffyDeliveryType(StrEnum):
    STATINA = DataDelivery.STATINA
    NO_DELIVERY = DataDelivery.NO_DELIVERY
