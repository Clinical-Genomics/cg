"""Tests for the BaseHandle class."""

from sqlalchemy.orm import Query

from cg.constants.devices import DeviceType, RevioNames
from cg.constants.subject import PhenotypeStatus
from cg.services.run_devices.pacbio.data_transfer_service.dto import (
    PacBioSampleSequencingMetricsDTO,
    PacBioSequencingRunDTO,
    PacBioSMRTCellDTO,
)
from cg.store.models import CaseSample, PacbioSMRTCellMetrics
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_latest_analyses_for_cases_query(
    analysis_store: Store, helpers, timestamp_now, timestamp_yesterday
):
    """Tests that analyses that are not latest are not returned."""

    # GIVEN an analysis a newer analysis exists
    case = helpers.add_case(analysis_store)
    analysis_oldest = helpers.add_analysis(
        analysis_store,
        case=case,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        delivery_reported_at=None,
    )
    analysis_store.session.add(analysis_oldest)
    analysis_store.session.commit()
    analysis_newest = helpers.add_analysis(
        analysis_store,
        case=case,
        started_at=timestamp_now,
        uploaded_at=timestamp_now,
        delivery_reported_at=None,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
    link: CaseSample = analysis_store.relate_sample(
        case=analysis_oldest.case, sample=sample, status=PhenotypeStatus.UNKNOWN
    )
    analysis_store.session.add(link)

    # WHEN calling the analyses_to_delivery_report
    analyses: Query = analysis_store._get_latest_analyses_for_cases_query()

    # THEN analyses is a query
    assert isinstance(analyses, Query)

    # THEN only the newest analysis should be returned
    assert analysis_newest in analyses
    assert analysis_oldest not in analyses


def test_update_pacbio_sample_reads(base_store: Store, helpers: StoreHelpers):
    # GIVEN a sample in the database with some initial reads and corresponding sample sequencing metrics
    initial_reads = 1000
    sample_id = "sample_id"
    helpers.add_sample(store=base_store, internal_id=sample_id, reads=initial_reads)
    pacbio_smrt_cell = PacBioSMRTCellDTO(type=DeviceType.PACBIO, internal_id="EA123")
    pacbio_smrt_cell = base_store.create_pac_bio_smrt_cell(pacbio_smrt_cell)
    base_store.commit_to_store()
    sequencing_run = base_store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, run_id="r123_123_123"
        )
    )
    smrt_cell_metrics: PacbioSMRTCellMetrics = helpers.add_pacbio_smrt_cell_metrics(
        store=base_store,
        id=1,
        device_id=pacbio_smrt_cell.id,
        sequencing_run=sequencing_run,
    )
    sample_run_metrics_dto = PacBioSampleSequencingMetricsDTO(
        sample_internal_id=sample_id,
        hifi_reads=initial_reads,
        hifi_yield=1,
        hifi_mean_read_length=1,
        hifi_median_read_quality="good",
        polymerase_mean_read_length=1,
    )
    base_store.create_pac_bio_sample_sequencing_run(
        sample_run_metrics_dto=sample_run_metrics_dto, smrt_cell_metrics=smrt_cell_metrics
    )
    base_store.commit_to_store()

    # GIVEN that there are additional sample sequencing metrics for the sample
    new_reads = 2000
    new_sample_run_metrics_dto = PacBioSampleSequencingMetricsDTO(
        sample_internal_id=sample_id,
        hifi_reads=new_reads,
        hifi_yield=1,
        hifi_mean_read_length=1,
        hifi_median_read_quality="good",
        polymerase_mean_read_length=1,
    )
    base_store.create_pac_bio_sample_sequencing_run(
        sample_run_metrics_dto=new_sample_run_metrics_dto, smrt_cell_metrics=smrt_cell_metrics
    )
    base_store.commit_to_store()

    # WHEN updating a samples reads
    base_store.recalculate_sample_reads_pacbio("sample_id")

    # THEN the sample should have updated the reads to the sum of the sample sequencing metrics
    assert base_store.get_sample_by_internal_id_strict(sample_id).reads == initial_reads + new_reads
