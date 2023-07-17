"""Test delivery report API methods."""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from _pytest.logging import LogCaptureFixture
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI

from cg.store import Store

from cg.meta.report.mip_dna import MipDNAReportAPI

from cg.constants import REPORT_GENDER
from cg.exc import DeliveryReportError
from cg.models.mip.mip_analysis import MipAnalysis
from cg.models.report.report import DataAnalysisModel, ReportModel, CustomerModel, CaseModel
from cg.models.report.sample import SampleModel, ApplicationModel, MethodsModel, TimestampModel
from cg.store.models import Analysis, FamilySample, Family
from tests.meta.report.helper import recursive_assert
from tests.store_helpers import StoreHelpers


def test_create_delivery_report(report_api_mip_dna: MipDNAReportAPI, case_mip_dna: Family):
    """Tests the creation of the rendered delivery report."""

    # GIVEN a pre-built case

    # WHEN extracting and rendering the report data
    delivery_report: str = report_api_mip_dna.create_delivery_report(
        case_id=case_mip_dna.internal_id,
        analysis_date=case_mip_dna.analyses[0].started_at,
        force_report=False,
    )

    # THEN check if the delivery report has been created
    assert len(delivery_report) > 0


def test_create_delivery_report_file(
    report_api_mip_dna: MipDNAReportAPI, case_mip_dna: Family, tmp_path: Path
):
    """Tests file generation containing the delivery report data."""

    # GIVEN a pre-built case

    # WHEN creating the report file
    created_report_file: Path = report_api_mip_dna.create_delivery_report_file(
        case_id=case_mip_dna.internal_id,
        directory=tmp_path,
        analysis_date=case_mip_dna.analyses[0].started_at,
        force_report=False,
    )

    # THEN check if a html report has been created and saved
    assert created_report_file.is_file()
    assert created_report_file.exists()


def test_render_delivery_report(report_api_mip_dna: MipDNAReportAPI, case_mip_dna: Family):
    """Tests delivery report rendering."""

    # GIVEN a generated report
    report_data: ReportModel = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )

    # WHEN rendering the report
    rendered_report: str = report_api_mip_dna.render_delivery_report(report_data.dict())

    # THEN validate rendered report
    assert len(rendered_report) > 0
    assert "html" in rendered_report


def test_get_validated_report_data(report_api_mip_dna: MipDNAReportAPI, case_mip_dna: Family):
    """Tests report data retrieval."""

    # GIVEN a valid case
    assert case_mip_dna
    assert case_mip_dna.links
    assert case_mip_dna.analyses

    # WHEN collecting the delivery data
    report_data: ReportModel = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )

    # THEN check collection of the nested report data and that the required fields are not empty
    report_data: ReportModel = report_api_mip_dna.validate_report_fields(
        case_mip_dna.internal_id, report_data, force_report=False
    )
    recursive_assert(report_data.dict())


def test_validate_report_empty_fields(
    report_api_mip_dna: MipDNAReportAPI, case_mip_dna: Family, caplog: LogCaptureFixture
):
    """Tests the validations of allowed empty report fields."""
    caplog.set_level(logging.INFO)

    # GIVEN a delivery report
    report_data: ReportModel = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )

    # WHEN the report has some allowed empty fields
    report_data.version = None
    report_data.customer.id = None
    report_data.case.samples[0].methods.library_prep = None

    # THEN check if the empty fields are identified
    report_data: ReportModel = report_api_mip_dna.validate_report_fields(
        case_mip_dna.internal_id, report_data, force_report=False
    )
    assert report_data
    assert "version" in caplog.text
    assert "id" in caplog.text
    assert "library_prep" in caplog.text


def test_validate_report_missing_fields(
    report_api_mip_dna: MipDNAReportAPI, case_mip_dna: Family, caplog: LogCaptureFixture
):
    """Tests the validations of empty required report fields."""

    # GIVEN a delivery report
    report_data: ReportModel = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )

    # WHEN the report contains some required empty fields
    report_data.accredited = None
    report_data.case.samples[0].metadata.million_read_pairs = None
    report_data.case.samples[1].metadata.duplicates = None

    # THEN test that the DeliveryReportError is raised when the report generation is not forced
    try:
        report_api_mip_dna.validate_report_fields(
            case_mip_dna.internal_id, report_data, force_report=False
        )
    except DeliveryReportError:
        assert "accredited" in caplog.text
        assert "duplicates" in caplog.text
        assert "accredited" in caplog.text


def test_get_validated_report_data_external_sample(
    report_api_mip_dna: MipDNAReportAPI, case_mip_dna: Family
):
    """Tests report data retrieval."""

    # GIVEN a delivery report with external sample data
    report_data: ReportModel = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )
    report_data.case.samples[0].timestamps.received_at = None
    report_data.case.samples[0].application.external = True

    # WHEN validating report fields
    report_data: ReportModel = report_api_mip_dna.validate_report_fields(
        case_mip_dna.internal_id, report_data, force_report=False
    )

    # THEN the validation should have been completed successfully
    assert report_data


def test_get_customer_data(report_api_mip_dna: MipDNAReportAPI, case_mip_dna: Family):
    """Checks that the retrieved customer data is the expected one."""

    # GIVEN a pre-built case

    # GIVEN an expected output
    expected_customer: dict = {
        "name": "Production",
        "id": "cust000",
        "invoice_address": "Test street",
        "scout_access": True,
    }

    # WHEN retrieving the customers data
    customer_data: CustomerModel = report_api_mip_dna.get_customer_data(case_mip_dna)

    # THEN check if the retrieved customer data corresponds to the expected one
    assert customer_data == expected_customer


def test_get_report_version_version(
    report_api_mip_dna: MipDNAReportAPI,
    store: Store,
    helpers: StoreHelpers,
    timestamp_yesterday: datetime,
):
    """Validates the extracted report versions of two analyses."""

    # GIVEN a specific set of analyses
    last_analysis: Analysis = helpers.add_analysis(store, completed_at=datetime.now())
    first_analysis: Analysis = helpers.add_analysis(
        store, last_analysis.family, completed_at=timestamp_yesterday
    )

    # WHEN retrieving the version
    last_analysis_version: int = report_api_mip_dna.get_report_version(last_analysis)
    first_analysis_version: int = report_api_mip_dna.get_report_version(first_analysis)

    # THEN check if the versions match
    assert last_analysis_version == 2
    assert first_analysis_version == 1


def test_get_case_data(
    report_api_mip_dna: MipDNAReportAPI,
    mip_analysis_api: MipDNAAnalysisAPI,
    case_mip_dna: Family,
    family_name: str,
):
    """Tests the extracted case data."""

    # GIVEN a pre-built case

    # GIVEN a mip analysis mock metadata
    mip_metadata: MipAnalysis = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)

    # WHEN retrieving case specific information
    case_data: CaseModel = report_api_mip_dna.get_case_data(
        case_mip_dna, case_mip_dna.analyses[0], mip_metadata
    )

    # THEN check if the case data is the expected one
    assert case_data.name == family_name
    assert case_data.data_analysis
    assert case_data.samples
    assert case_data.applications


def test_get_samples_data(
    report_api_mip_dna: MipDNAReportAPI,
    mip_analysis_api: MipDNAAnalysisAPI,
    case_mip_dna: Family,
    case_samples_data: List[FamilySample],
    lims_samples: List[dict],
):
    """Validates the retrieved sample data."""

    # GIVEN a pre-built case

    # GIVEN an expected output
    expected_lims_data: dict = lims_samples[0]
    expected_sample_data: FamilySample = case_samples_data[0]

    # GIVEN a mip analysis mock metadata
    mip_metadata: MipAnalysis = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)

    # WHEN extracting the samples of a specific case
    samples_data: SampleModel = report_api_mip_dna.get_samples_data(case_mip_dna, mip_metadata)[0]

    # THEN assert that the retrieved sample is the expected one
    assert samples_data.name == str(expected_sample_data.sample.name)
    assert samples_data.id == str(expected_sample_data.sample.internal_id)
    assert samples_data.ticket == str(expected_sample_data.sample.original_ticket)
    assert samples_data.status == str(expected_sample_data.status)
    assert samples_data.gender == REPORT_GENDER.get(str(expected_sample_data.sample.sex))
    assert samples_data.source == str(expected_lims_data.get("source"))
    assert samples_data.tumour == "Nej"
    assert samples_data.application
    assert samples_data.methods
    assert samples_data.metadata
    assert samples_data.timestamps


def test_get_lims_sample(
    report_api_mip_dna: MipDNAReportAPI,
    case_samples_data: List[FamilySample],
    lims_samples: List[dict],
):
    """Tests lims data extraction."""

    # GIVEN a family samples instance

    # GIVEN an expected output
    expected_lims_data: dict = lims_samples[0]

    # WHEN getting the sample data from lims
    lims_data: dict = report_api_mip_dna.get_lims_sample(case_samples_data[0].sample.internal_id)

    # THEN check if the extracted lims information match the expected one
    assert lims_data == expected_lims_data


def test_get_sample_application_data(
    report_api_mip_dna: MipDNAReportAPI,
    case_samples_data: List[FamilySample],
    lims_samples: List[dict],
):
    """Tests sample application data extraction."""

    # GIVEN a lims sample instance

    # GIVEN the expected application data
    expected_application_data: dict = case_samples_data[0].sample.to_dict().get("application")

    # WHEN retrieving application data from status DB
    application_data: ApplicationModel = report_api_mip_dna.get_sample_application_data(
        lims_samples[0]
    )

    # THEN verify that the application data corresponds to what is expected
    assert application_data.tag == str(expected_application_data.get("tag"))
    assert application_data.version == str(lims_samples[0].get("application_version"))
    assert application_data.prep_category == str(expected_application_data.get("prep_category"))
    assert application_data.description == str(expected_application_data.get("description"))
    assert application_data.limitations == str(expected_application_data.get("limitations"))
    assert application_data.accredited == expected_application_data.get("is_accredited")


def test_get_unique_applications(
    report_api_mip_dna: MipDNAReportAPI, mip_analysis_api: MipDNAAnalysisAPI, case_mip_dna: Family
):
    """Tests unique applications filtering."""

    # GIVEN a list of samples sharing the same application
    mip_metadata: MipAnalysis = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)
    samples: List[SampleModel] = report_api_mip_dna.get_samples_data(case_mip_dna, mip_metadata)

    # WHEN calling the application filtering function
    unique_applications: List[ApplicationModel] = report_api_mip_dna.get_unique_applications(
        samples
    )

    # THEN check that the same sample applications were filtered out
    assert len(unique_applications) == 1


def test_get_sample_methods_data(
    report_api_mip_dna: MipDNAReportAPI, case_samples_data: List[FamilySample]
):
    """Tests sample methods retrieval from lims."""

    # GIVEN a sample ID
    sample_id: str = case_samples_data[0].sample.to_dict().get("internal_id")

    # GIVEN an expected output
    expected_sample_methods = {
        "library_prep": "CG002 - End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free DNA)",
        "sequencing": "CG002 - Cluster Generation (HiSeq X)",
    }

    # WHEN calling the method extraction function
    sample_methods: MethodsModel = report_api_mip_dna.get_sample_methods_data(sample_id)

    # THEN check the agreement between expected and extracted values
    assert sample_methods == expected_sample_methods


def test_get_case_analysis_data(
    report_api_mip_dna: MipDNAReportAPI, mip_analysis_api: MipDNAAnalysisAPI, case_mip_dna: Family
):
    """Tests data analysis parameters retrieval."""

    # GIVEN a pre-built case

    # GIVEN a mip analysis mock metadata
    mip_metadata: MipAnalysis = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)

    # WHEN retrieving analysis information
    case_analysis_data: DataAnalysisModel = report_api_mip_dna.get_case_analysis_data(
        case_mip_dna, case_mip_dna.analyses[0], mip_metadata
    )

    # THEN check if the retrieved analysis data is correct
    assert case_analysis_data.pipeline == "mip-dna"
    assert case_analysis_data.panels == "IEM, EP"
    assert case_analysis_data.scout_files


def test_get_sample_timestamp_data(
    report_api_mip_dna: MipDNAReportAPI,
    case_samples_data: List[FamilySample],
    timestamp_yesterday: datetime,
):
    """Checks that the sample timestamp information is correctly retrieved from StatusDB."""

    # GIVEN a mock sample data

    # GIVEN an expected output
    expected_case_samples_data = {
        "ordered_at": str((datetime.now() - timedelta(days=3)).date()),
        "received_at": str((datetime.now() - timedelta(days=2)).date()),
        "prepared_at": str(timestamp_yesterday.date()),
        "sequenced_at": str(timestamp_yesterday.date()),
    }

    # WHEN extracting the timestamp data associated to a specific sample
    sample_timestamp_data: TimestampModel = report_api_mip_dna.get_sample_timestamp_data(
        case_samples_data[0].sample
    )

    # THEN check if the dates are correctly retrieved
    assert sample_timestamp_data == expected_case_samples_data
