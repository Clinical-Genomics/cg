from cg.server.endpoints.sequencing_metrics.dtos import PacbioSequencingMetricsRequest
from cg.services.sample_run_metrics_service.dtos import PacbioSequencingMetricsDTO
from cg.services.sample_run_metrics_service.sample_run_metrics_service import (
    SampleRunMetricsService,
)
from cg.store.models import PacbioSampleSequencingMetrics


def test_get_metrics_for_flow_cell(
    sample_run_metrics_service: SampleRunMetricsService,
    novaseq_x_flow_cell_id: str,
):
    # GIVEN an existing flow cell with sequencing metrics

    # WHEN fetching the metrics for the flow cell
    metrics = sample_run_metrics_service.get_illumina_metrics(novaseq_x_flow_cell_id)

    # THEN the metrics should be returned
    assert metrics


def test_get_pacbio_metrics(sample_run_metrics_service: SampleRunMetricsService):
    # GIVEN a SampleRunMetricsService and a database containing Pacbio data

    # WHEN fetching all PacbioSampleSequencingMetrics
    metrics_request = PacbioSequencingMetricsRequest()
    metrics: list[PacbioSequencingMetricsDTO] = sample_run_metrics_service.get_pacbio_metrics(
        metrics_request
    )

    # THEN all metrics should be returned
    assert (
        len(metrics)
        == sample_run_metrics_service.store._get_query(table=PacbioSampleSequencingMetrics).count()
    )


def test_get_pacbio_metrics_by_sample_internal_id(
    sample_run_metrics_service: SampleRunMetricsService, pacbio_barcoded_sample_internal_id: str
):
    # GIVEN a SampleRunMetricsService and a database containing Pacbio data

    # WHEN fetching a specific PacbioSampleSequencingMetrics
    metrics_request = PacbioSequencingMetricsRequest(sample_id=pacbio_barcoded_sample_internal_id)
    sequencing_metrics: list[PacbioSequencingMetricsDTO] = (
        sample_run_metrics_service.get_pacbio_metrics(metrics_request)
    )

    # THEN metrics should be returned for the specified sample
    assert [
        metrics.sample_id == pacbio_barcoded_sample_internal_id for metrics in sequencing_metrics
    ]


def test_get_pacbio_metrics_by_non_existent_sample_internal_id(
    sample_run_metrics_service: SampleRunMetricsService,
):
    # GIVEN a SampleRunMetricsService and a database containing Pacbio data

    # WHEN fetching a specific PacbioSampleSequencingMetrics
    metrics_request = PacbioSequencingMetricsRequest(sample_id="I do not exist")
    metrics: list[PacbioSequencingMetricsDTO] = sample_run_metrics_service.get_pacbio_metrics(
        metrics_request
    )

    # THEN metrics should not be returned
    assert not metrics


def test_get_pacbio_metrics_by_smrt_cell_id(
    sample_run_metrics_service: SampleRunMetricsService,
):
    # GIVEN a SampleRunMetricsService and a database containing Pacbio data

    # WHEN fetching a specific PacbioSampleSequencingMetrics
    metrics_request = PacbioSequencingMetricsRequest(smrt_cell_ids=["internal_id"])
    sequencing_metrics: list[PacbioSequencingMetricsDTO] = (
        sample_run_metrics_service.get_pacbio_metrics(metrics_request)
    )

    # THEN metrics should be returned for the specified smrt_cell
    assert [metrics.smrt_cell_id == "internal_id" for metrics in sequencing_metrics]


def test_get_pacbio_metrics_by_non_existent_smrt_cell_id(
    sample_run_metrics_service: SampleRunMetricsService,
):
    # GIVEN a SampleRunMetricsService and a database containing Pacbio data

    # WHEN fetching a specific PacbioSampleSequencingMetrics
    metrics_request = PacbioSequencingMetricsRequest(smrt_cell_ids=["I do not exist"])
    metrics: list[PacbioSequencingMetricsDTO] = sample_run_metrics_service.get_pacbio_metrics(
        metrics_request
    )

    # THEN no metrics should be returned
    assert not metrics
