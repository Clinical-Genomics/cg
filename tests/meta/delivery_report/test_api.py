"""Tests for the delivery report API."""

from pathlib import Path
from typing import Any

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture

from cg.constants import Workflow
from cg.exc import DeliveryReportError
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.models.analysis import AnalysisModel
from cg.models.delivery_report.metadata import SampleMetadataModel
from cg.models.delivery_report.report import (
    ReportModel,
    CustomerModel,
    CaseModel,
    DataAnalysisModel,
)
from cg.models.delivery_report.sample import (
    SampleModel,
    ApplicationModel,
    MethodsModel,
    TimestampModel,
)
from cg.store.models import Case, Analysis, Sample


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_delivery_report_html(request: FixtureRequest, workflow: Workflow):
    """Test rendering of the delivery report for different workflows."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case object
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # WHEN generating the delivery report HTML
    delivery_report_html: str = delivery_report_api.get_delivery_report_html(
        case_id=case_id, analysis_date=case.analyses[0].started_at, force=False
    )

    # THEN it should generate a valid HTML string
    assert delivery_report_html
    assert "<!DOCTYPE html>" in delivery_report_html


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def write_delivery_report_file(request: FixtureRequest, workflow: Workflow, tmp_path: Path):
    """Test writing of the delivery report for different workflows."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case object
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    delivery_report_file: Path = delivery_report_api.write_delivery_report_file(
        case_id=case.internal_id,
        directory=tmp_path,
        analysis_date=case.analyses[0].started_at,
        force=False,
    )

    # THEN check if the HTML delivery report has been generated and written
    assert delivery_report_file.is_file()


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_render_delivery_report(request: FixtureRequest, workflow: Workflow):
    """Test delivery report HTML rendering."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case object
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN some report data
    report_data: ReportModel = delivery_report_api.get_report_data(
        case_id=case_id, analysis_date=case.analyses[0].started_at
    )

    # WHEN rendering the report
    rendered_report: str = delivery_report_api.render_delivery_report(report_data.model_dump())

    # THEN validate rendered report
    assert rendered_report
    assert "<!DOCTYPE html>" in rendered_report


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_report_data(request: FixtureRequest, workflow: Workflow):
    """Test extraction of the data necessary to render the delivery report."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # WHEN extracting the report data
    report_data: ReportModel = delivery_report_api.get_report_data(
        case_id=case_id, analysis_date=case.analyses[0].started_at
    )

    # THEN the report model should have been populated and the data validated
    assert report_data
    assert isinstance(report_data, ReportModel)


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_validate_report_data(request: FixtureRequest, workflow: Workflow):
    """Test retrieval and validation of the delivery report data."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a report data model
    report_data: ReportModel = delivery_report_api.get_report_data(
        case_id=case_id, analysis_date=case.analyses[0].started_at
    )

    # WHEN validating the delivery report data
    report_data_validated: ReportModel = delivery_report_api.validate_report_data(
        case_id=case_id, report_data=report_data, force=False
    )

    # THEN the delivery report data should have been validated, with all the required fields present
    assert report_data_validated
    assert isinstance(report_data_validated, ReportModel)


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_validate_report_data_empty_optional_fields(
    request: FixtureRequest, workflow: Workflow, caplog: LogCaptureFixture
):
    """Test delivery report validations with allowed empty report fields."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a delivery report data model
    report_data: ReportModel = delivery_report_api.get_report_data(
        case_id, case.analyses[0].started_at
    )

    # GIVEN empty optional delivery report fields
    report_data.version = None
    report_data.customer.id = None
    report_data.case.samples[0].methods.library_prep = None

    # WHEN validating the delivery report data
    report_data: ReportModel = delivery_report_api.validate_report_data(
        case_id=case_id, report_data=report_data, force=False
    )

    # THEN the validation should not fail
    assert report_data

    # THEN the missing values should be logged
    assert "Empty report fields:" in caplog.text
    assert "version" in caplog.text
    assert "id" in caplog.text
    assert "library_prep" in caplog.text


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_validate_report_data_empty_required_fields(
    request: FixtureRequest, workflow: Workflow, caplog: LogCaptureFixture
):
    """Tests the validations of empty required delivery report fields."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a delivery report data model
    report_data: ReportModel = delivery_report_api.get_report_data(
        case_id, case.analyses[0].started_at
    )

    # GIVEN empty required delivery report fields
    report_data.accredited = None
    report_data.case.samples[0].metadata.million_read_pairs = None
    report_data.case.samples[0].metadata.duplicates = None

    # THEN a DeliveryReportError should be raised
    with pytest.raises(DeliveryReportError):
        delivery_report_api.validate_report_data(
            case_id=case_id, report_data=report_data, force=False
        )

    # THEN the required missing values should be logged
    assert "Missing data:" in caplog.text
    assert "accredited" in caplog.text
    assert "million_read_pairs" in caplog.text
    assert "duplicates" in caplog.text


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_validate_report_data_empty_required_fields_force(
    request: FixtureRequest, workflow: Workflow, caplog: LogCaptureFixture
):
    """Tests the validations of empty required delivery report fields with a force flag."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a delivery report data model
    report_data: ReportModel = delivery_report_api.get_report_data(
        case_id, case.analyses[0].started_at
    )

    # GIVEN empty required delivery report fields
    report_data.accredited = None
    report_data.case.samples[0].metadata.million_read_pairs = None
    report_data.case.samples[0].metadata.duplicates = None

    # THEN a DeliveryReportError should not be raised
    report_data_validated: ReportModel = delivery_report_api.validate_report_data(
        case_id=case_id, report_data=report_data, force=True
    )

    # THEN the delivery report data should have been validated despite missing required fields
    assert report_data_validated
    assert isinstance(report_data_validated, ReportModel)


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_validate_report_data_external_sample(request: FixtureRequest, workflow: Workflow):
    """Tests report data validation for a case with an external sample."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a delivery report data model
    report_data: ReportModel = delivery_report_api.get_report_data(
        case_id, case.analyses[0].started_at
    )

    # GIVEN a case with an external sample
    report_data.case.samples[0].timestamps.received_at = None
    report_data.case.samples[0].application.external = True

    # WHEN validating the delivery report fields
    report_data: ReportModel = delivery_report_api.validate_report_data(
        case_id=case_id, report_data=report_data, force=False
    )

    # THEN the delivery report data should have been successfully validated
    assert report_data


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_customer_data(request: FixtureRequest, workflow: Workflow):
    """Checks that the retrieved customer data is the expected one."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # WHEN retrieving the customers data
    customer_data: CustomerModel = delivery_report_api.get_customer_data(case)

    # THEN the customer model should have been successfully populated
    assert customer_data
    assert customer_data.name
    assert customer_data.id
    assert customer_data.invoice_address


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_report_version(request: FixtureRequest, workflow: Workflow):
    """Test report version extraction from an analysis object."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN an analysis object
    analysis: Analysis = case.analyses[0]

    # WHEN retrieving the delivery report version
    delivery_report_version: int = delivery_report_api.get_report_version(analysis)

    # THEN the first version should be returned
    assert delivery_report_version == 1


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_case_data(request: FixtureRequest, workflow: Workflow):
    """Test report version extraction from an analysis object."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN workflow specific analysis metadata
    analysis_metadata: AnalysisModel = delivery_report_api.analysis_api.get_latest_metadata(case_id)

    # WHEN retrieving case data
    case_data: CaseModel = delivery_report_api.get_case_data(
        case=case, analysis=case.analyses[0], analysis_metadata=analysis_metadata
    )

    # THEN the case delivery report model should have been populated
    assert case_data
    assert case_data.name
    assert case_data.data_analysis
    assert case_data.samples
    assert case_data.applications


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_samples_data(request: FixtureRequest, workflow: Workflow):
    """Test retrieval of sample data."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN workflow specific analysis metadata
    analysis_metadata: AnalysisModel = delivery_report_api.analysis_api.get_latest_metadata(case_id)

    # WHEN extracting the samples of a specific case
    samples_data: SampleModel = delivery_report_api.get_samples_data(
        case=case, analysis_metadata=analysis_metadata
    )[0]

    # THEN assert that the retrieved sample model has been correctly build
    assert samples_data
    assert samples_data.name
    assert samples_data.id
    assert samples_data.ticket
    assert samples_data.status
    assert samples_data.sex
    assert samples_data.source
    assert samples_data.tumour
    assert samples_data.application
    assert samples_data.methods
    assert samples_data.metadata
    assert samples_data.timestamps


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_sample_application(request: FixtureRequest, workflow: Workflow):
    """Test sample application data extraction."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a sample
    sample: Sample = case.samples[0]

    # GIVEN a LIMS sample
    lims_sample: dict[str, Any] = delivery_report_api.analysis_api.lims_api.sample(
        sample.internal_id
    )

    # WHEN retrieving application data from Statusdb
    application_data: ApplicationModel = delivery_report_api.get_sample_application(
        sample=sample, lims_sample=lims_sample
    )

    # THEN verify that the application data corresponds to what is expected
    assert application_data
    assert application_data.tag
    assert application_data.version
    assert application_data.prep_category
    assert application_data.description
    assert application_data.limitations
    assert application_data.accredited


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_unique_applications(request: FixtureRequest, workflow: Workflow):
    """Test unique applications filtering."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN workflow specific analysis metadata
    analysis_metadata: AnalysisModel = delivery_report_api.analysis_api.get_latest_metadata(case_id)

    # GIVEN a list of delivery report sample models
    samples: list[SampleModel] = delivery_report_api.get_samples_data(
        case=case, analysis_metadata=analysis_metadata
    )

    # WHEN filtering unique applications
    unique_applications: list[ApplicationModel] = delivery_report_api.get_unique_applications(
        samples
    )

    # THEN check that the same sample applications were filtered out
    assert len(unique_applications) == 1


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_sample_methods_data(request: FixtureRequest, workflow: Workflow, sample_id: str):
    """Test sample methods retrieval from LIMS."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a sample ID

    # WHEN extracting the methods metadata
    sample_methods: MethodsModel = delivery_report_api.get_sample_methods_data(sample_id)

    # THEN check sample methods data have been correctly retrieved
    assert sample_methods
    assert sample_methods.library_prep
    assert sample_methods.sequencing


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_case_analysis_data(request: FixtureRequest, workflow: Workflow):
    """Test data analysis retrieval."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # WHEN retrieving a case analysis
    case_analysis_data: DataAnalysisModel = delivery_report_api.get_case_analysis_data(
        case, case.analyses[0]
    )

    # THEN the case analysis data model has been populated
    assert case_analysis_data
    assert case_analysis_data.workflow
    assert case_analysis_data.panels
    assert case_analysis_data.scout_files


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_sample_timestamp_data(request: FixtureRequest, workflow: Workflow):
    """Test that the sample timestamp information is correctly retrieved from StatusDB."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a sample
    sample: Sample = case.samples[0]

    # WHEN extracting the timestamp data associated to a specific sample
    sample_timestamp_data: TimestampModel = delivery_report_api.get_sample_timestamp_data(sample)

    # THEN check if the dates are correctly retrieved
    assert sample_timestamp_data
    assert sample_timestamp_data.ordered_at
    assert sample_timestamp_data.received_at
    assert sample_timestamp_data.prepared_at
    assert sample_timestamp_data.reads_updated_at


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_get_sample_metadata(request: FixtureRequest, workflow: Workflow):
    """Test sample metadata extraction."""

    # GIVEN a delivery report API
    delivery_report_api: DeliveryReportAPI = request.getfixturevalue(
        f"{workflow}_delivery_report_api"
    )

    # GIVEN a case
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")
    case: Case = delivery_report_api.analysis_api.status_db.get_case_by_internal_id(case_id)

    # GIVEN a sample
    sample: Sample = case.samples[0]

    # GIVEN workflow specific analysis metadata
    analysis_metadata: AnalysisModel = delivery_report_api.analysis_api.get_latest_metadata(case_id)

    # WHEN retrieving the sample metadata
    sample_metadata: SampleMetadataModel = delivery_report_api.get_sample_metadata(
        case=case, sample=sample, analysis_metadata=analysis_metadata
    )

    # THEN check that the sample metadata has been correctly retrieved
    assert sample_metadata
