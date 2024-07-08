import pytest

from cg.constants.pacbio import CCSAttributeIDs
from cg.services.pacbio.metrics.models import HiFiMetrics


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
