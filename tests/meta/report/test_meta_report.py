import os
from pathlib import Path

from cg.meta.report.api import ReportAPI


def test_init():
    ReportAPI(lims_api='lims', db='analysis_store', chanjo_api='chanjo', analysis_api='analysis',
              scout_api='scout')


def test_collect_delivery_data(report_api):
    # GIVEN an initialised report_api and a family ready for delivery report creation

    # WHEN collecting delivery data for a certain
    delivery_data = report_api._get_delivery_data(family_id='yellowhog')

    # THEN all data for the delivery report should have been collected
    assert delivery_data['report_version']
    assert delivery_data['previous_report_version']
    assert delivery_data['family']
    assert delivery_data['customer_obj'].name
    assert delivery_data['today'].date()
    assert delivery_data['panels']

    assert delivery_data['customer_obj'].invoice_address
    assert delivery_data['customer_obj'].scout_access
    assert delivery_data['accredited']

    for application in delivery_data['application_objs']:
        assert application['tag']
        assert application['description']
        assert application['limitations']

    assert delivery_data['samples']

    for sample in delivery_data['samples']:
        assert sample['name']
        assert sample['id']
        assert sample['sex']
        assert sample['status']
        assert sample['source']
        assert sample['ticket']
        assert sample['application']
        assert sample['received']

        assert sample['order_date']
        assert sample['prep_method']
        assert sample['prep_date']
        assert sample['capture_kit']
        assert sample['sequencing_method']
        assert sample['sequencing_date']
        assert sample['delivery_method']
        assert sample['delivery_date']

        assert sample['million_read_pairs']
        assert sample['mapped_reads']
        assert sample['target_coverage']
        assert sample['target_completeness']
        assert sample['duplicates']
        assert sample['processing_time']
        assert sample['analysis_sex']

    assert delivery_data['mip_version']
    assert delivery_data['genome_build']


def test_get_application_data_from_status_db(lims_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_application_data_from_status_db
    samples = lims_samples
    application_data = report_api._get_application_data_from_status_db(samples)

    # THEN
    # the generated data has a property apptags with a value
    assert application_data['application_objs']

    # the generated data has a property accredited with a value
    assert application_data['accredited'] is True


def test_get_status_from_status_db(report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_application_data_from_status_db
    samples = report_api._fetch_family_samples_from_status_db('yellowhog')

    # THEN
    # the samples contain a status
    for sample in samples:
        assert sample['status']
        assert sample['status'] != 'N/A'


def test_incorporate_lims_methods(lims_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_and_add_lims_methods
    samples = lims_samples
    report_api._incorporate_lims_methods(samples)

    # THEN certain metrics should have been calculated

    # each sample has a property library_prep_method with a value
    for sample in samples:
        assert sample['prep_method']

    # each sample has a property sequencing_method with a value
    for sample in samples:
        assert sample['sequencing_method']

    # each sample has a property delivery_method with a value
    for sample in samples:
        assert sample['delivery_method']


def test_render_delivery_report(report_api):
    # GIVEN proper qc data from an analysis exist
    report_data = report_api._get_delivery_data(family_id='yellowhog')

    # WHEN rendering a report from that data
    rendered_report = ReportAPI._render_delivery_report(report_data)

    # THEN a html report with certain data should have been rendered
    assert len(rendered_report) > 0


def test_create_delivery_report(report_api):
    # GIVEN initialized ReportAPI

    # WHEN rendering a report from that data
    created_report = report_api.create_delivery_report(family_id='yellowhog')

    # THEN a html report with certain data should have been rendered
    assert len(created_report) > 0


def test_create_delivery_report_file(report_api: ReportAPI):
    # GIVEN initialized ReportAPI

    # WHEN rendering a report from that data
    created_report_file = report_api.create_delivery_report_file(family_id='yellowhog',
                                                                 file_path=Path('.'))

    # THEN a html report with certain data should have been created on disk
    assert os.path.isfile(created_report_file.name)
    os.unlink(created_report_file.name)


def test_incorporate_coverage_data(report_api, lims_samples):
    # GIVEN an initialised report_api and the chanjo_api does not return what we want
    report_api.chanjo._sample_coverage_returns_none = True
    samples = lims_samples

    # WHEN failing to get latest trending data for a family
    report_api._incorporate_coverage_data(samples=samples, panels='dummyPanel')

    # THEN there should be a log entry about this
    for sample in samples:
        lims_id = sample['id']
        assert not sample.get('target_coverage')
        assert not sample.get('target_completeness')
        lims_id_found_in_warnings = False
        for warning in report_api.LOG.get_warnings():
            lims_id_found_in_warnings = lims_id in warning or lims_id_found_in_warnings
        assert lims_id_found_in_warnings


def test_fetch_family_samples_from_status_db(report_api):
    # GIVEN an initialised report_api and the db returns samples without reads
    report_api.db.family_samples_returns_no_reads = True

    # WHEN fetching status data
    samples = report_api._fetch_family_samples_from_status_db(family_id='yellowhog')

    # THEN the report data should have N/A where it report sample reads
    assert samples
    for sample in samples:
        assert sample.get('million_read_pairs') == 'N/A'


def test_fetch_no_capture_kit_from_status_db(report_api):

    # GIVEN an initialised report_api and the db returns samples without capture kit
    report_api.db.samples_returns_no_capture_kit = True

    # WHEN fetching status data
    samples = report_api._fetch_family_samples_from_status_db(family_id='yellowhog')

    # THEN the report data should have N/A where it reports capture_kit
    assert samples
    for sample in samples:
        assert sample.get('capture_kit') == 'N/A'


def test_fetch_capture_kit_from_status_db(report_api):

    # GIVEN an initialised report_api and the db returns samples with capture kit

    # WHEN fetching status data
    samples = report_api._fetch_family_samples_from_status_db(family_id='yellowhog')

    # THEN the report data should have capture kit
    assert samples
    for sample in samples:
        assert sample.get('capture_kit') == 'GMSmyeloid'


def test_data_analysis_kit_from_status_db(report_api):

    # GIVEN an initialised report_api and the db returns samples with data_analysis

    # WHEN fetching status data
    samples = report_api._fetch_family_samples_from_status_db(family_id='yellowhog')

    # THEN the report data should have capture kit
    assert samples
    for sample in samples:
        assert sample.get('bioinformatic_analysis') == 'PIM'


def test_get_application_data_from_status_db(lims_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_application_data_from_status_db
    samples = lims_samples
    application_data = report_api._get_application_data_from_status_db(samples)

    # THEN
    # the generated data has a property apptags with a value
    assert application_data['application_objs']


def test_get_application_data_from_status_db_all_accredited(lims_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api
    report_api.db._application_accreditation = True

    # WHEN fetch_application_data_from_status_db
    samples = lims_samples
    application_data = report_api._get_application_data_from_status_db(samples)

    # THEN the generated data has a property accredited with a value
    assert application_data['accredited'] is True


def test_get_application_data_from_status_db_none_accredited(lims_samples, report_api):
    # GIVEN data from an analysed case and an initialised report_api
    report_api.db._application_accreditation = False

    # WHEN fetch_application_data_from_status_db
    samples = lims_samples
    application_data = report_api._get_application_data_from_status_db(samples)

    # THEN the generated data has a property accredited with a value
    assert application_data['accredited'] is False
