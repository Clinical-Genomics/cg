from typing import Any

import pytest

from cg.constants.pacbio import (
    CCSAttributeIDs,
    ControlAttributeIDs,
    LoadingAttributesIDs,
    PolymeraseDataAttributeIDs,
    SmrtLinkDatabasesIDs,
)
from cg.services.pacbio.metrics.models import (
    ControlMetrics,
    HiFiMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    SmrtlinkDatasetsMetrics,
)


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


@pytest.fixture
def pac_bio_polymerase_metrics() -> PolymeraseMetrics:
    data: dict[str, Any] = {
        PolymeraseDataAttributeIDs.MEAN_READ_LENGTH: 82182,
        PolymeraseDataAttributeIDs.READ_LENGTH_N50: 153250,
        PolymeraseDataAttributeIDs.MEAN_LONGEST_SUBREAD_LENGTH: 18466,
        PolymeraseDataAttributeIDs.LONGEST_SUBREAD_LENGTH_N50: 22250,
    }
    return PolymeraseMetrics.model_validate(data, from_attributes=True)


@pytest.fixture
def pac_bio_smrtlink_databases_metrics() -> SmrtlinkDatasetsMetrics:
    data: dict[str, Any] = {
        SmrtLinkDatabasesIDs.BIO_SAMPLE_NAME: "1247014000119",
        SmrtLinkDatabasesIDs.CELL_ID: "EA094834",
        SmrtLinkDatabasesIDs.CELL_INDEX: 0,
        SmrtLinkDatabasesIDs.MOVIE_NAME: "m84202_240522_135641_s1",
        SmrtLinkDatabasesIDs.PATH: "/srv/cg_data/pacbio/r84202_20240522_133539/1_A01/pb_formats/m84202_240522_135641_s1.hifi_reads.consensusreadset.xml",
        SmrtLinkDatabasesIDs.WELL_NAME: "A01",
        SmrtLinkDatabasesIDs.WELL_SAMPLE_NAME: "1247014000119",
    }
    return SmrtlinkDatasetsMetrics.model_validate(data, from_attributes=True)
