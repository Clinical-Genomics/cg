from enum import StrEnum

from cg.constants import DataDelivery


class NalloDeliveryType(StrEnum):
    ANALYSIS = DataDelivery.ANALYSIS_FILES
    ANALYSIS_SCOUT = DataDelivery.ANALYSIS_SCOUT
    NO_DELIVERY = DataDelivery.NO_DELIVERY
    SCOUT = DataDelivery.SCOUT
    RAW_DATA_ANALYSIS = DataDelivery.RAW_DATA_ANALYSIS
    RAW_DATA_ANALYSIS_SCOUT = DataDelivery.RAW_DATA_ANALYSIS_SCOUT
    RAW_DATA_SCOUT = DataDelivery.RAW_DATA_SCOUT
