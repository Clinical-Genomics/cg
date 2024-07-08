from typing import Any

import pytest

from cg.constants.pacbio import CCSAttributeIDs, ControlAttributeIDs, LoadingAttributesIDs
from cg.services.pacbio.metrics.models import ControlMetrics, HiFiMetrics, ProductivityMetrics


@pytest.fixture
def pac_bio_hifi_metrics() -> HiFiMetrics:
    data: dict[str, Any] = {
        CCSAttributeIDs.NUMBER_OF_READS: 6580977,
        CCSAttributeIDs.TOTAL_NUMBER_OF_BASES: 106192944185,
        CCSAttributeIDs.MEAN_READ_LENGTH: 16136,
        CCSAttributeIDs.MEDIAN_READ_LENGTH: 16205,
        CCSAttributeIDs.READ_LENGTH_N50: 18372,
        CCSAttributeIDs.MEDIAN_ACCURACY: "Q34",
        CCSAttributeIDs.PERCENT_Q30: 0.9318790946286002,
    }
    return HiFiMetrics.model_validate(data, from_attributes=True)


@pytest.fixture
def pac_bio_control_metrics() -> ControlMetrics:
    data: dict[str, Any] = {
        ControlAttributeIDs.NUMBER_OF_READS: 2750,
        ControlAttributeIDs.MEAN_READ_LENGTH: 57730,
        ControlAttributeIDs.PERCENT_MEAN_READ_CONCORDANCE: 0.906334,
        ControlAttributeIDs.PERCENT_MODE_READ_CONCORDANCE: 0.91,
    }
    return ControlMetrics.model_validate(data, from_attributes=True)


@pytest.fixture
def pac_bio_productivity_metrics() -> ProductivityMetrics:
    data: dict[str, Any] = {
        LoadingAttributesIDs.PRODUCTIVE_ZMWS: 25165824,
        LoadingAttributesIDs.P_0: 10012557,
        LoadingAttributesIDs.P_1: 15048838,
        LoadingAttributesIDs.P_2: 104429,
    }
    return ProductivityMetrics.model_validate(data, from_attributes=True)
