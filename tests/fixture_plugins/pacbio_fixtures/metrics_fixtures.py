"""Fixtures for PacBio metrics objects."""

import pytest

from cg.constants.pacbio import (
    BarcodeMetricsAliases,
    CCSAttributeIDs,
    ControlAttributeIDs,
    LoadingAttributesIDs,
    PolymeraseDataAttributeIDs,
    SampleMetricsAliases,
    SmrtLinkDatabasesIDs,
)
from cg.services.run_devices.pacbio.metrics_parser.models import (
    BarcodeMetrics,
    ControlMetrics,
    PacBioMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    ReadMetrics,
    SampleMetrics,
    SmrtlinkDatasetsMetrics,
)


@pytest.fixture
def pac_bio_read_metrics() -> ReadMetrics:
    data: dict[str, any] = {
        CCSAttributeIDs.HIFI_READS: 6580977,
        CCSAttributeIDs.HIFI_YIELD: 106275091861,
        CCSAttributeIDs.HIFI_MEAN_READ_LENGTH: 16148,
        CCSAttributeIDs.HIFI_MEDIAN_READ_LENGTH: 16218,
        CCSAttributeIDs.HIFI_READ_LENGTH_N50: 16218,
        CCSAttributeIDs.HIFI_MEDIAN_READ_QUALITY: 34,
        CCSAttributeIDs.PERCENT_Q30: 93.2,
        CCSAttributeIDs.FAILED_READS: 281284,
        CCSAttributeIDs.FAILED_YIELD: 4862922407,
        CCSAttributeIDs.FAILED_MEAN_READ_LENGTH: 17288,
    }
    return ReadMetrics.model_validate(data)


@pytest.fixture
def pac_bio_control_metrics() -> ControlMetrics:
    data: dict[str, any] = {
        ControlAttributeIDs.NUMBER_OF_READS: 2750,
        ControlAttributeIDs.MEAN_READ_LENGTH: 57730,
        ControlAttributeIDs.PERCENT_MEAN_READ_CONCORDANCE: 0.906334,
        ControlAttributeIDs.PERCENT_MODE_READ_CONCORDANCE: 0.91,
    }
    return ControlMetrics.model_validate(data)


@pytest.fixture
def pac_bio_productivity_metrics() -> ProductivityMetrics:
    data: dict[str, any] = {
        LoadingAttributesIDs.PRODUCTIVE_ZMWS: 25165824,
        LoadingAttributesIDs.P_0: 10012557,
        LoadingAttributesIDs.P_1: 15048838,
        LoadingAttributesIDs.P_2: 104429,
    }
    return ProductivityMetrics.model_validate(data)


@pytest.fixture
def pac_bio_polymerase_metrics() -> PolymeraseMetrics:
    data: dict[str, any] = {
        PolymeraseDataAttributeIDs.MEAN_READ_LENGTH: 82182,
        PolymeraseDataAttributeIDs.READ_LENGTH_N50: 153250,
        PolymeraseDataAttributeIDs.MEAN_LONGEST_SUBREAD_LENGTH: 18466,
        PolymeraseDataAttributeIDs.LONGEST_SUBREAD_LENGTH_N50: 22250,
    }
    return PolymeraseMetrics.model_validate(data)


@pytest.fixture
def pac_bio_smrtlink_databases_metrics(
    smrt_cell_internal_id: str, pac_bio_sample_internal_id: str, pac_bio_1_a01_cell_full_name: str
) -> SmrtlinkDatasetsMetrics:
    data: dict[str, any] = {
        SmrtLinkDatabasesIDs.BIO_SAMPLE_NAME: pac_bio_sample_internal_id,
        SmrtLinkDatabasesIDs.CELL_ID: smrt_cell_internal_id,
        SmrtLinkDatabasesIDs.CELL_INDEX: 0,
        SmrtLinkDatabasesIDs.MOVIE_NAME: pac_bio_1_a01_cell_full_name,
        SmrtLinkDatabasesIDs.PATH: "/srv/cg_data/pacbio/r84202_20240522_133539/1_A01/pb_formats/m84202_240522_135641_s1.hifi_reads.consensusreadset.xml",
        SmrtLinkDatabasesIDs.RUN_COMPLETED_AT: "2024-05-24T02:21:20.970Z",
        SmrtLinkDatabasesIDs.WELL_NAME: "A01",
        SmrtLinkDatabasesIDs.WELL_SAMPLE_NAME: pac_bio_sample_internal_id,
    }
    return SmrtlinkDatasetsMetrics.model_validate(data)


@pytest.fixture
def pacbio_barcodes_metrics(
    barcoded_smrt_cell_internal_id: str,
    pacbio_barcoded_sample_internal_id: str,
    pacbio_barcoded_1_c01_cell_full_name: str,
) -> BarcodeMetrics:
    data: dict[str, any] = {
        BarcodeMetricsAliases.BARCODED_HIFI_READS: 7785983,
        BarcodeMetricsAliases.BARCODED_HIFI_READS_PERCENTAGE: 0.9962486409672513,
        BarcodeMetricsAliases.BARCODED_HIFI_YIELD: 114676808325,
        BarcodeMetricsAliases.BARCODED_HIFI_YIELD_PERCENTAGE: 0.9963122400514475,
        BarcodeMetricsAliases.BARCODED_MEAN_READ_LENGTH: 14728,
        BarcodeMetricsAliases.UNBARCODED_HIFI_READS: 29318,
        BarcodeMetricsAliases.UNBARCODED_HIFI_YIELD: 424465869,
        BarcodeMetricsAliases.UNBARCODED_HIFI_MEAN_READ_LENGTH: 14477,
    }
    return BarcodeMetrics.model_validate(data)


@pytest.fixture
def pacbio_barcoded_sample_metrics(
    barcoded_smrt_cell_internal_id: str,
    pacbio_barcoded_sample_internal_id: str,
    pacbio_barcoded_1_c01_cell_full_name: str,
) -> SampleMetrics:
    data: dict[str, any] = {
        SampleMetricsAliases.BARCODE_NAME: "bc2004--bc2004",
        SampleMetricsAliases.HIFI_MEAN_READ_LENGTH: 14728,
        SampleMetricsAliases.HIFI_READ_QUALITY: "Q35",
        SampleMetricsAliases.HIFI_READS: 7785983,
        SampleMetricsAliases.HIFI_YIELD: 114676808325,
        SampleMetricsAliases.PLOYMERASE_READ_LENGTH: 163451,
        SampleMetricsAliases.SAMPLE_NAME: pacbio_barcoded_sample_internal_id,
    }
    return SampleMetrics.model_validate(data)


@pytest.fixture
def pacbio_unassigned_sample_metrics(
    barcoded_smrt_cell_internal_id: str,
    pacbio_unassigned_sample_internal_id: str,
    pacbio_barcoded_1_c01_cell_full_name: str,
) -> SampleMetrics:
    data: dict[str, any] = {
        SampleMetricsAliases.BARCODE_NAME: "Not Barcoded",
        SampleMetricsAliases.HIFI_MEAN_READ_LENGTH: 14477,
        SampleMetricsAliases.HIFI_READ_QUALITY: "Q28",
        SampleMetricsAliases.HIFI_READS: 29318,
        SampleMetricsAliases.HIFI_YIELD: 424465869,
        SampleMetricsAliases.PLOYMERASE_READ_LENGTH: 142228,
        SampleMetricsAliases.SAMPLE_NAME: pacbio_unassigned_sample_internal_id,
    }
    return SampleMetrics.model_validate(data)


@pytest.fixture
def pac_bio_metrics(
    pac_bio_read_metrics: ReadMetrics,
    pac_bio_control_metrics: ControlMetrics,
    pac_bio_productivity_metrics: ProductivityMetrics,
    pac_bio_polymerase_metrics: PolymeraseMetrics,
    pac_bio_smrtlink_databases_metrics: SmrtlinkDatasetsMetrics,
    pacbio_barcodes_metrics: BarcodeMetrics,
    pacbio_barcoded_sample_metrics: SampleMetrics,
    pacbio_unassigned_sample_metrics: SampleMetrics,
) -> PacBioMetrics:
    return PacBioMetrics(
        read=pac_bio_read_metrics,
        control=pac_bio_control_metrics,
        productivity=pac_bio_productivity_metrics,
        polymerase=pac_bio_polymerase_metrics,
        dataset_metrics=pac_bio_smrtlink_databases_metrics,
        barcodes=pacbio_barcodes_metrics,
        samples=[pacbio_barcoded_sample_metrics, pacbio_unassigned_sample_metrics],
    )
