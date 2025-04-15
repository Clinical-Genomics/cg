from enum import StrEnum

from cg.constants import DataDelivery


class NalloDeliveryType(StrEnum):
    ANALYSIS = DataDelivery.ANALYSIS_FILES
    ANALYSIS_SCOUT = DataDelivery.ANALYSIS_SCOUT
    NO_DELIVERY = DataDelivery.NO_DELIVERY
    SCOUT = DataDelivery.SCOUT
