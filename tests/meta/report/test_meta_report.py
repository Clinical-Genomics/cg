
from cg.meta.report.api import ReportAPI


def test_collect_delivery_data(report_api):
    # GIVEN an initialised report_api

    # WHEN collecting delivery data for a certain
    delivery_data = report_api._get_delivery_data(customer_id='cust000', family_id='yellowhog')

    # THEN all data for the delivery report should have been collected
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

        assert sample['prep_method']
        assert sample['sequencing_method']
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


def test_incorporate_delivery_date_from_lims(lims_samples, report_api):

    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_and_add_delivery_date_from_lims
    samples = lims_samples
    report_api._incorporate_delivery_date_from_lims(samples)

    # THEN
    # each sample has a property processing_time with a value of the days between received_at and
    #   delivery_date
    for sample in samples:
        assert sample['delivery_date']


def test_incorporate_processing_time_from_lims(lims_samples, report_api):

    # GIVEN data from an analysed case and an initialised report_api

    # WHEN fetch_and_add_delivery_date_from_lims
    samples = lims_samples
    report_api._incorporate_processing_time_from_lims(samples)

    # THEN
    # each sample has a property processing_time with a value of the days between received_at and
    #   delivery_date
    for sample in samples:
        assert sample['processing_time']


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


def test_get_customer_from_status_db(report_api):
    # GIVEN data from an analysed case and an initialised report_api
    customer_id = 'cust002'

    # WHEN generating_qc_data
    customer_obj = report_api._get_customer_from_status_db(customer_id)

    # THEN customer properties should be available

    # customer is the the full customer object in the database
    assert customer_obj.name


def test_render_delivery_report(report_api):
    # GIVEN proper qc data from an analysis exist
    report_data = report_api._get_delivery_data(customer_id='cust002', family_id='yellowhog')

    # WHEN rendering a report from that data
    rendered_report = ReportAPI._render_delivery_report(report_data)

    # THEN a html report with certain data should have been rendered
    assert len(rendered_report) > 0


def test_create_delivery_report(report_api):
    # GIVEN initialized ReportAPI

    # WHEN rendering a report from that data
    created_report = report_api.create_delivery_report(customer_id='cust002', family_id='yellowhog')

    # THEN a html report with certain data should have been rendered
    assert len(created_report) > 0
