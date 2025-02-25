"""Fixtures for PacBio metrics objects."""

import pytest

from cg.constants.pacbio import (
    BarcodeMetricsAliases,
    CCSAttributeAliases,
    ControlAttributeAliases,
    LoadingAttributesAliases,
    PolymeraseDataAttributeAliases,
    SampleMetricsAliases,
    SmrtLinkDatabasesAliases,
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
        CCSAttributeAliases.HIFI_READS: 7815301,
        CCSAttributeAliases.HIFI_YIELD: 115338856495,
        CCSAttributeAliases.HIFI_MEAN_READ_LENGTH: 14758,
        CCSAttributeAliases.HIFI_MEDIAN_READ_LENGTH: 14679,
        CCSAttributeAliases.HIFI_READ_LENGTH_N50: 14679,
        CCSAttributeAliases.HIFI_MEDIAN_READ_QUALITY: 35,
        CCSAttributeAliases.PERCENT_Q30: 93.10000000000001,
        CCSAttributeAliases.FAILED_READS: 469053,
        CCSAttributeAliases.FAILED_YIELD: 7404831038,
        CCSAttributeAliases.FAILED_MEAN_READ_LENGTH: 15786,
    }
    return ReadMetrics.model_validate(data)


@pytest.fixture
def pac_bio_control_metrics() -> ControlMetrics:
    data: dict[str, any] = {
        ControlAttributeAliases.NUMBER_OF_READS: 2368,
        ControlAttributeAliases.MEAN_READ_LENGTH: 69936,
        ControlAttributeAliases.PERCENT_MEAN_READ_CONCORDANCE: 0.90038,
        ControlAttributeAliases.PERCENT_MODE_READ_CONCORDANCE: 0.91,
    }
    return ControlMetrics.model_validate(data)


@pytest.fixture
def pac_bio_productivity_metrics() -> ProductivityMetrics:
    data: dict[str, any] = {
        LoadingAttributesAliases.PRODUCTIVE_ZMWS: 25165824,
        LoadingAttributesAliases.P_0: 6257733,
        LoadingAttributesAliases.P_1: 18766925,
        LoadingAttributesAliases.P_2: 141166,
    }
    return ProductivityMetrics.model_validate(data)


@pytest.fixture
def pac_bio_polymerase_metrics() -> PolymeraseMetrics:
    data: dict[str, any] = {
        PolymeraseDataAttributeAliases.MEAN_READ_LENGTH: 85641,
        PolymeraseDataAttributeAliases.READ_LENGTH_N50: 168750,
        PolymeraseDataAttributeAliases.MEAN_LONGEST_SUBREAD_LENGTH: 18042,
        PolymeraseDataAttributeAliases.LONGEST_SUBREAD_LENGTH_N50: 21750,
    }
    return PolymeraseMetrics.model_validate(data)


@pytest.fixture
def pac_bio_smrtlink_databases_metrics(
    barcoded_smrt_cell_internal_id: str,
    pacbio_barcoded_1_c01_cell_full_name: str,
) -> SmrtlinkDatasetsMetrics:
    data: dict[str, any] = {
        SmrtLinkDatabasesAliases.CELL_ID: barcoded_smrt_cell_internal_id,
        SmrtLinkDatabasesAliases.CELL_INDEX: 2,
        SmrtLinkDatabasesAliases.MOVIE_NAME: pacbio_barcoded_1_c01_cell_full_name,
        SmrtLinkDatabasesAliases.PATH: "/srv/cg_data/pacbio/r84202_20240913_121403/1_C01/pb_formats/m84202_240913_162115_s3.hifi_reads.consensusreadset.xml",
        SmrtLinkDatabasesAliases.RUN_COMPLETED_AT: "2024-09-15T14:11:32.418Z",
        SmrtLinkDatabasesAliases.WELL_NAME: "C01",
        SmrtLinkDatabasesAliases.WELL_SAMPLE_NAME: "2023-17834-05",
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
        SampleMetricsAliases.POLYMERASE_READ_LENGTH: 163451,
        SampleMetricsAliases.SAMPLE_INTERNAL_ID: pacbio_barcoded_sample_internal_id,
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
        SampleMetricsAliases.POLYMERASE_READ_LENGTH: 142228,
        SampleMetricsAliases.SAMPLE_INTERNAL_ID: pacbio_unassigned_sample_internal_id,
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
