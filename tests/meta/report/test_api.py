import os
from datetime import datetime, timedelta

from tests.meta.report.helper import recursive_assert


def test_create_delivery_report(report_api_mip_dna, case_mip_dna):
    """Tests the creation of the rendered delivery report"""

    # GIVEN a pre-built case

    # WHEN extracting and rendering the report data
    delivery_report = report_api_mip_dna.create_delivery_report(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )

    # THEN check if the delivery report has been created
    assert len(delivery_report) > 0


def test_create_delivery_report_file(report_api_mip_dna, case_mip_dna, tmp_path):
    """Tests file generation containing the delivery report data"""

    # GIVEN a pre-built case

    # WHEN creating the report file
    created_report_file = report_api_mip_dna.create_delivery_report_file(
        case_id=case_mip_dna.internal_id,
        file_path=tmp_path,
        analysis_date=case_mip_dna.analyses[0].started_at,
    )

    # THEN check if an html report has been created and saved
    assert os.path.isfile(created_report_file.name)


def test_render_delivery_report(report_api_mip_dna, case_mip_dna):
    """Tests delivery report rendering"""

    # GIVEN a generated report
    report_data = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )

    # WHEN rendering the report
    rendered_report = report_api_mip_dna.render_delivery_report(report_data.dict())

    # THEN validate rendered report
    assert len(rendered_report) > 0
    assert "html" in rendered_report


def test_get_report_data(report_api_mip_dna, case_mip_dna):
    """Tests report data retrieval"""

    # GIVEN a valid case
    assert case_mip_dna
    assert case_mip_dna.links
    assert case_mip_dna.analyses

    # WHEN collecting the delivery data
    report_data = report_api_mip_dna.get_report_data(
        case_mip_dna.internal_id, case_mip_dna.analyses[0].started_at
    )

    # THEN check collection of the nested report data
    recursive_assert(report_data.dict())


def test_get_customer_data(report_api_mip_dna, case_mip_dna):
    """Checks that the retrieved customer data is the expected one"""

    # GIVEN a pre-built case

    # GIVEN an expected output
    expected_customer = {
        "name": "Production",
        "id": "cust000",
        "invoice_address": "Test street",
        "scout_access": True,
    }

    # WHEN retrieving the customers data
    customer_data = report_api_mip_dna.get_customer_data(case_mip_dna)

    # THEN check if the retrieved customer data corresponds to the expected one
    assert customer_data == expected_customer


def test_get_report_version_version(report_api_mip_dna, store, helpers):
    """Validates the extracted report versions of two analyses"""

    # GIVEN a specific set of analyses
    last_analysis = helpers.add_analysis(store, completed_at=datetime.now())
    yesterday = datetime.now() - timedelta(days=1)
    first_analysis = helpers.add_analysis(store, last_analysis.family, completed_at=yesterday)

    # WHEN retrieving the version
    last_analysis_version = report_api_mip_dna.get_report_version(last_analysis)
    first_analysis_version = report_api_mip_dna.get_report_version(first_analysis)

    # THEN check if the versions match
    assert last_analysis_version == 2
    assert first_analysis_version == 1


def test_get_case_data(report_api_mip_dna, mip_analysis_api, case_mip_dna, family_name):
    """Tests the extracted case data"""

    # GIVEN a pre-built case

    # GIVEN a mip analysis mock metadata
    mip_metadata = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)

    # WHEN retrieving case specific information
    case_data = report_api_mip_dna.get_case_data(
        case_mip_dna, case_mip_dna.analyses[0], mip_metadata
    )

    # THEN check if the case data is the expected one
    assert case_data.name == family_name
    assert case_data.data_analysis
    assert case_data.samples
    assert case_data.applications


def test_get_samples_data(
    report_api_mip_dna, mip_analysis_api, case_mip_dna, case_samples_data, lims_samples
):
    """Validates the retrieved sample data"""

    # GIVEN a pre-built case

    # GIVEN an expected output
    expected_lims_data = lims_samples[0]
    expected_sample_data = case_samples_data[0]

    # GIVEN a mip analysis mock metadata
    mip_metadata = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)

    # print(mip_metadata)

    # WHEN extracting the samples of a specific case
    samples_data = report_api_mip_dna.get_samples_data(case_mip_dna, mip_metadata)

    # THEN assert that the retrieved sample is the expected one
    assert samples_data[0].name == str(expected_lims_data.get("name"))
    assert samples_data[0].id == str(expected_sample_data.sample.internal_id)
    assert samples_data[0].ticket == str(expected_sample_data.sample.ticket_number)
    assert samples_data[0].status == str(expected_sample_data.status)
    assert samples_data[0].gender == str(expected_lims_data.get("sex"))
    assert samples_data[0].source == str(expected_lims_data.get("source"))
    assert samples_data[0].tumour == "Nej"
    assert samples_data[0].application
    assert samples_data[0].methods
    assert samples_data[0].metadata
    assert samples_data[0].timestamp


def test_get_lims_sample(report_api_mip_dna, case_samples_data, lims_samples):
    """Tests lims data extraction"""

    # GIVEN a family samples instance

    # GIVEN an expected output
    expected_lims_data = lims_samples[0]

    # WHEN getting the sample data from lims
    lims_data = report_api_mip_dna.get_lims_sample(case_samples_data[0].sample.internal_id)

    # THEN check if the extracted lims information match the expected one
    assert lims_data == expected_lims_data


def test_get_sample_application_data(report_api_mip_dna, case_samples_data, lims_samples):
    """Tests sample application data extraction"""

    # GIVEN a lims sample instance

    # GIVEN the expected application data
    expected_application_data = case_samples_data[0].sample.to_dict().get("application")

    # WHEN retrieving application data from status DB
    application_data = report_api_mip_dna.get_sample_application_data(lims_samples[0])

    # THEN verify that the application data corresponds to what is expected
    assert application_data.tag == str(expected_application_data.get("tag"))
    assert application_data.version == str(lims_samples[0].get("application_version"))
    assert application_data.prep_category == str(expected_application_data.get("prep_category"))
    assert application_data.description == str(expected_application_data.get("description"))
    assert application_data.limitations == str(expected_application_data.get("limitations"))
    assert application_data.accredited == expected_application_data.get("is_accredited")


def test_get_unique_applications(report_api_mip_dna, mip_analysis_api, case_mip_dna):
    """Tests unique applications filtering"""

    # GIVEN a list of samples sharing the same application
    mip_metadata = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)
    samples = report_api_mip_dna.get_samples_data(case_mip_dna, mip_metadata)

    # WHEN calling the application filtering function
    unique_applications = report_api_mip_dna.get_unique_applications(samples)

    # THEN check that the same sample applications were filtered out
    assert len(unique_applications) == 1


def test_get_sample_methods_data(report_api_mip_dna, case_samples_data):
    """Tests sample methods retrieval from lims"""

    # GIVEN a sample ID
    sample_id = case_samples_data[0].sample.to_dict().get("internal_id")

    # GIVEN an expected output
    expected_sample_methods = {
        "library_prep": "CG002 - End repair Size selection A-tailing and Adapter ligation (TruSeq PCR-free DNA)",
        "sequencing": "CG002 - Cluster Generation (HiSeq X)",
    }

    # WHEN calling the method extraction function
    sample_methods = report_api_mip_dna.get_sample_methods_data(sample_id)

    # THEN check the agreement between expected and extracted values
    assert sample_methods == expected_sample_methods


def test_get_case_analysis_data(report_api_mip_dna, mip_analysis_api, case_mip_dna):
    """Tests data analysis parameters retrieval"""

    # GIVEN a pre-built case

    # GIVEN a mip analysis mock metadata
    mip_metadata = mip_analysis_api.get_latest_metadata(case_mip_dna.internal_id)

    # GIVEN an expected data analysis output
    expected_case_analysis_data = {
        "customer_pipeline": "mip-dna",
        "pipeline": "mip-dna",
        "pipeline_version": "1.0",
        "type": "wgs",
        "genome_build": "hg19",
        "variant_callers": "N/A",
        "panels": "IEM, EP",
    }

    # WHEN retrieving analysis information
    case_analysis_data = report_api_mip_dna.get_case_analysis_data(
        case_mip_dna, case_mip_dna.analyses[0], mip_metadata
    )

    # THEN check if the retrieved analysis data is correct
    assert case_analysis_data == expected_case_analysis_data


def test_get_sample_timestamp_data(report_api_mip_dna, case_samples_data):
    """Checks that the sample timestamp information is correctly retrieved from StatusDB"""

    # GIVEN a mock sample data

    # GIVEN an expected output
    yesterday = str((datetime.now() - timedelta(days=1)).date())
    expected_case_samples_data = {
        "ordered_at": str((datetime.now() - timedelta(days=3)).date()),
        "received_at": str((datetime.now() - timedelta(days=2)).date()),
        "prepared_at": yesterday,
        "sequenced_at": yesterday,
        "delivered_at": str((datetime.now()).date()),
        "processing_days": "2",
    }

    # WHEN extracting the timestamp data associated to a specific sample
    sample_timestamp_data = report_api_mip_dna.get_sample_timestamp_data(
        case_samples_data[0].sample
    )

    # THEN check if the dates are correctly retrieved
    assert sample_timestamp_data == expected_case_samples_data


def test_get_processing_days(report_api_mip_dna, sample_store, helpers):
    """Tests processing dates calculation"""

    # GIVEN a specific sample received 5 days ago
    sample = helpers.add_sample(sample_store)
    sample.received_at = datetime.now() - timedelta(days=5)
    sample.delivered_at = datetime.now()

    # WHEN calling the processing dates calculation method
    processing_days = report_api_mip_dna.get_processing_days(sample)

    # THEN check if the days to deliver are correctly calculated
    assert processing_days == 5


def test_get_processing_days_none(report_api_mip_dna, sample_store, helpers):
    """Tests processing dates calculation when a date value is missing"""

    # GIVEN a specific sample without a timestamp value
    sample = helpers.add_sample(sample_store)
    sample.received_at = None

    # WHEN calling the processing dates calculation method
    processing_days = report_api_mip_dna.get_processing_days(sample)

    # THEN check if None is returned
    assert processing_days is None
