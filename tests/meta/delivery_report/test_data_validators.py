"""Tests delivery report data validation helpers."""

import math
from pathlib import Path
from unittest.mock import Mock, create_autospec

from cg.apps.coverage import ChanjoAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import NA_FIELD, DataDelivery, Workflow
from cg.meta.delivery.delivery import DeliveryAPI
from cg.meta.delivery_report.data_validators import (
    get_empty_report_data,
    get_million_read_pairs,
    get_missing_report_data,
)
from cg.meta.delivery_report.raredisease import RarediseaseDeliveryReportAPI
from cg.meta.delivery_report.rnafusion import RnafusionDeliveryReportAPI
from cg.meta.delivery_report.tomte import TomteDeliveryReportAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.meta.workflow.tomte import TomteAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.delivery.delivery import DeliveryFile
from cg.models.delivery_report.report import ReportModel
from cg.models.orders.sample_base import SexEnum
from cg.store.models import Analysis, Application, ApplicationVersion, Case, CaseSample, Sample
from cg.store.store import Store
from tests.meta.delivery_report.conftest import (
    EXPECTED_RNAFUSION_QC_TABLE_WTS,
    EXPECTED_TOMTE_QC_TABLE_WTS,
)


def test_get_empty_report_data(
    raredisease_delivery_report_api: RarediseaseDeliveryReportAPI,
    raredisease_case_id: str,
    sample_id: str,
):
    """Test extraction of empty report fields."""

    # GIVEN a delivery report API

    # GIVEN an analysis
    analysis: Analysis = create_autospec(Analysis)
    analysis.comment = "comment"
    analysis.workflow = "raredisease"
    analysis.workflow_version = "1.0.0"

    # GIVEN a sample ID

    # GIVEN a delivery report data model
    report_data: ReportModel = raredisease_delivery_report_api.get_report_data(
        case_id=raredisease_case_id, analysis=analysis
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


def test_get_delivery_report_html_rnafusion(rnafusion_analysis: NextflowAnalysis):
    # GIVEN a store with a RNAFusion case linked to a sample
    application_version = create_autospec(
        ApplicationVersion, application=create_autospec(Application)
    )
    sample: Sample = create_autospec(
        Sample,
        sex=SexEnum.female,
        internal_id="sample_id",
        application_version=application_version,
        is_tumour=False,
    )
    sample.name = "sample_name"
    case: Case = create_autospec(
        Case,
        data_analysis=Workflow.RNAFUSION,
        data_delivery=DataDelivery.ANALYSIS_FILES,
        internal_id="case_id",
        sample=[sample],
    )

    store: Store = create_autospec(Store)
    store.get_case_by_internal_id = Mock(return_value=case)
    case_sample = create_autospec(CaseSample, sample=sample, case=case)
    store.get_case_samples_by_case_id = Mock(return_value=[case_sample])

    # GIVEN a Delivery API
    delivery_api: DeliveryAPI = create_autospec(DeliveryAPI)
    delivery_api.is_analysis_delivery = Mock(return_value=True)
    delivery_api.get_analysis_case_delivery_files = Mock(
        return_value=[
            create_autospec(
                DeliveryFile, destination_path=Path("destination"), source_path=Path("source")
            )
        ]
    )

    # GIVEN a LIMS API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.has_sample_passed_initial_qc = Mock(return_value=True)

    # GIVEN a RNAFusion Analysis API
    analysis_api = create_autospec(
        RnafusionAnalysisAPI,
        chanjo_api=create_autospec(ChanjoAPI),
        delivery_api=delivery_api,
        housekeeper_api=create_autospec(HousekeeperAPI),
        lims_api=lims_api,
        scout_api=create_autospec(ScoutAPI),
        status_db=store,
        workflow=Workflow.RNAFUSION,
    )
    analysis_api.get_latest_metadata = Mock(return_value=rnafusion_analysis)

    # GIVEN a RNAFusion delivery report API
    delivery_report_api = RnafusionDeliveryReportAPI(analysis_api)

    # WHEN generating a delivery report
    delivery_report: str = delivery_report_api.get_delivery_report_html(
        create_autospec(
            Analysis,
            comment="some comment",
            workflow=Workflow.RNAFUSION,
            workflow_version="1.0.0",
        ),
        force=False,
    )

    # THEN the report is generated as expected
    assert EXPECTED_RNAFUSION_QC_TABLE_WTS in delivery_report


def test_get_delivery_report_html_tomte(tomte_analysis: NextflowAnalysis):
    # GIVEN a store with a Tomte case linked to a sample
    application_version = create_autospec(
        ApplicationVersion, application=create_autospec(Application)
    )
    sample: Sample = create_autospec(
        Sample,
        sex=SexEnum.female,
        internal_id="sample_id",
        application_version=application_version,
        is_tumour=False,
    )
    sample.name = "sample_name"
    case: Case = create_autospec(
        Case,
        data_analysis=Workflow.TOMTE,
        data_delivery=DataDelivery.ANALYSIS_FILES,
        internal_id="case_id",
        sample=[sample],
    )

    store: Store = create_autospec(Store)
    store.get_case_by_internal_id = Mock(return_value=case)
    case_sample = create_autospec(CaseSample, sample=sample, case=case)
    store.get_case_samples_by_case_id = Mock(return_value=[case_sample])

    # GIVEN a Delivery API
    delivery_api: DeliveryAPI = create_autospec(DeliveryAPI)
    delivery_api.is_analysis_delivery = Mock(return_value=True)
    delivery_api.get_analysis_case_delivery_files = Mock(
        return_value=[
            create_autospec(
                DeliveryFile, destination_path=Path("destination"), source_path=Path("source")
            )
        ]
    )

    # GIVEN a LIMS API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.has_sample_passed_initial_qc = Mock(return_value=True)

    # GIVEN a Tomte Analysis API
    analysis_api = create_autospec(
        TomteAnalysisAPI,
        chanjo_api=create_autospec(ChanjoAPI),
        delivery_api=delivery_api,
        housekeeper_api=create_autospec(HousekeeperAPI),
        lims_api=lims_api,
        scout_api=create_autospec(ScoutAPI),
        status_db=store,
        workflow=Workflow.TOMTE,
    )
    analysis_api.get_latest_metadata = Mock(return_value=tomte_analysis)

    # GIVEN a RNAFusion delivery report API
    delivery_report_api = TomteDeliveryReportAPI(analysis_api)

    # WHEN generating a delivery report
    delivery_report: str = delivery_report_api.get_delivery_report_html(
        create_autospec(
            Analysis,
            comment="some comment",
            workflow=Workflow.TOMTE,
            workflow_version="1.0.0",
        ),
        force=False,
    )

    # THEN the report is generated as expected
    assert EXPECTED_TOMTE_QC_TABLE_WTS in delivery_report


def test_get_missing_report_data(
    raredisease_delivery_report_api: RarediseaseDeliveryReportAPI,
    raredisease_case_id: str,
    sample_id: str,
):
    """Test getting missing report fields."""

    # GIVEN a delivery report API

    # GIVEN an analysis
    analysis: Analysis = create_autospec(Analysis)
    analysis.comment = "comment"
    analysis.workflow = "raredisease"
    analysis.workflow_version = "1.0.0"

    # GIVEN a sample ID

    # GIVEN a report data model
    report_data: ReportModel = raredisease_delivery_report_api.get_report_data(
        case_id=raredisease_case_id, analysis=analysis
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
