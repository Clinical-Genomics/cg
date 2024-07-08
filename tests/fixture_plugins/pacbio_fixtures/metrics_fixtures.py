import pytest

from cg.constants.pacbio import CCSAttributeIDs, ControlAttributeIDs
from cg.services.pacbio.metrics.models import ControlMetrics, HiFiMetrics


@pytest.fixture
def pac_bio_hifi_metrics():
    data = {
        CCSAttributeIDs.NUMBER_OF_READS: 6580977,
        CCSAttributeIDs.TOTAL_NUMBER_OF_BASES: 106192944185,
        CCSAttributeIDs.MEAN_READ_LENGTH: 16136,
        CCSAttributeIDs.MEDIAN_READ_LENGTH: 16205,
        CCSAttributeIDs.READ_LENGTH_N50: 18372,
        CCSAttributeIDs.MEDIAN_ACCURACY: "Q34",
        CCSAttributeIDs.PERCENT_Q30: 0.9318790946286002,
    }
    return HiFiMetrics(**data)


@pytest.fixture
def pac_bio_control_metrics():
    data = {
        ControlAttributeIDs.NUMBER_OF_READS: 2750,
        ControlAttributeIDs.MEAN_READ_LENGTH: 57730,
        ControlAttributeIDs.PERCENT_MEAN_READ_CONCORDANCE: 0.906334,
        ControlAttributeIDs.PERCENT_MODE_READ_CONCORDANCE: 0.91,
    }
    return ControlMetrics(**data)
