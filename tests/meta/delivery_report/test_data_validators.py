"""Tests delivery report data validation helpers."""

import math

from cg.constants import NA_FIELD
from cg.meta.delivery_report.data_validators import (
    get_empty_report_data,
    get_missing_report_data,
    get_million_read_pairs,
)
from cg.meta.delivery_report.raredisease import RarediseaseDeliveryReportAPI
from cg.models.delivery_report.report import ReportModel
from cg.store.models import Case


def test_get_empty_report_data(
    raredisease_delivery_report_api: RarediseaseDeliveryReportAPI,
    raredisease_case_id: str,
    sample_id: str,
):
    """Test extraction of empty report fields."""

    # GIVEN a delivery report API

    # GIVEN a case object
    case: Case = raredisease_delivery_report_api.analysis_api.status_db.get_case_by_internal_id(
        raredisease_case_id
    )

    # GIVEN a sample ID

    # GIVEN a delivery report data model
    report_data: ReportModel = raredisease_delivery_report_api.get_report_data(
        case_id=raredisease_case_id, analysis_date=case.analyses[0].started_at
    )

    # GIVEN empty fields
    report_data.version = None
    report_data.accredited = None
    report_data.customer.id = NA_FIELD
    report_data.customer.scout_access = False
    report_data.case.samples[0].methods.library_prep = ""
    report_data.case.samples[0].metadata.million_read_pairs = None
    report_data.case.samples[0].metadata.duplicates = None

    # WHEN retrieving the missing data
    empty_report_data: dict = get_empty_report_data(report_data)

    # THEN assert that the empty fields are correctly retrieved
    assert "version" in empty_report_data["report"]
    assert "accredited" in empty_report_data["report"]
    assert "id" in empty_report_data["customer"]
    assert "scout_access" not in empty_report_data["customer"]
    assert "library_prep" in empty_report_data["methods"][sample_id]
    assert "million_read_pairs" in empty_report_data["metadata"][sample_id]
    assert "duplicates" in empty_report_data["metadata"][sample_id]


def test_get_missing_report_data(
    raredisease_delivery_report_api: RarediseaseDeliveryReportAPI,
    raredisease_case_id: str,
    sample_id: str,
):
    """Test getting missing report fields."""

    # GIVEN a delivery report API

    # GIVEN a case object
    case: Case = raredisease_delivery_report_api.analysis_api.status_db.get_case_by_internal_id(
        raredisease_case_id
    )

    # GIVEN a sample ID

    # GIVEN a report data model
    report_data: ReportModel = raredisease_delivery_report_api.get_report_data(
        raredisease_case_id, case.analyses[0].started_at
    )

    # GIVEN a dictionary of report empty fields and a list of required MIP DNA report fields
    empty_fields = {
        "report": ["version", "accredited"],
        "customer": ["id"],
        "methods": {sample_id: ["library_prep"]},
        "metadata": {
            sample_id: ["bait_set", "million_read_pairs", "duplicates"],
        },
    }

    required_fields: dict = raredisease_delivery_report_api.get_required_fields(report_data.case)

    # WHEN retrieving the missing data
    missing_fields: dict = get_missing_report_data(
        empty_fields=empty_fields, required_fields=required_fields
    )

    # THEN assert that the required fields are identified
    assert "version" not in missing_fields["report"]
    assert "accredited" in missing_fields["report"]
    assert "customer" not in missing_fields
    assert "methods" not in missing_fields
    assert "million_read_pairs" in missing_fields["metadata"][sample_id]
    assert "duplicates" in missing_fields["metadata"][sample_id]
    assert "bait_set" not in missing_fields["metadata"][sample_id]


def test_get_million_read_pairs():
    """Test millions read pairs calculation."""

    # GIVEN a number of sequencing reads and its representation in millions of read pairs
    sample_reads = 1_200_000_000
    expected_million_read_pairs = sample_reads / 2_000_000

    # WHEN obtaining the number of reds in millions of read pairs
    million_read_pairs: float = get_million_read_pairs(sample_reads)

    # THEN the expected value should match the calculated one
    assert math.isclose(million_read_pairs, expected_million_read_pairs)


def test_get_million_read_pairs_zero_input():
    """Tests millions read pairs calculation when the sample reads number is zero."""

    # GIVEN zero as number of reads
    sample_reads = 0

    # WHEN retrieving the number of reds in millions of read pairs
    million_read_pairs: float = get_million_read_pairs(sample_reads)

    # THEN the obtained value should be zero
    assert math.isclose(million_read_pairs, 0.0)
