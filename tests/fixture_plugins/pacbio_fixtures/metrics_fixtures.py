import pytest

from cg.services.pacbio_services.pacbio_metrics_service.models import HiFiMetrics


@pytest.fixture
def pacbio_hifi_metrics():
    data = {
        "ccs2.number_of_ccs_reads": 6580977,
        "ccs2.total_number_of_ccs_bases": 106192944185,
        "ccs2.mean_ccs_readlength": 16136,
        "ccs2.median_ccs_readlength": 16205,
        "ccs2.ccs_readlength_n50": 18372,
        "ccs2.median_accuracy": "Q34",
        "ccs2.percent_ccs_bases_q30": 0.9318790946286002,
    }
    return HiFiMetrics(**data)
