
from cg.meta.report.api import ReportAPI


def test_collect_delivery_data(report_api):
    # GIVEN an initialised report_api

    # WHEN collecting delivery data for a certain
    delivery_data = report_api.collect_delivery_data(customer='cust002',family='yellowhog')
    print(delivery_data)

    # THEN all data for the delivery report should have been collected
    assert delivery_data['family']
    assert delivery_data['customer'].name
    assert delivery_data['today'].date()
    assert delivery_data['panels']

    assert delivery_data['customer'].invoice_address
    assert delivery_data['customer'].scout_access
    assert delivery_data['accredited']

    for application in delivery_data['applications']:
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
        assert sample['project']
        assert sample['application']
        assert sample['received']

        assert sample['prep_method']
        assert sample['sequencing_method']
        assert sample['delivery_method']

        assert sample['delivery_date'].date()
        assert sample['read_pairs']
        assert sample['mapped']
        assert sample['target_coverage']
        assert sample['target_completeness']
        assert sample['duplicates']
        assert sample['processing_time']
        assert sample['sex_predicted']

    assert delivery_data['pipeline_version']
    assert delivery_data['reference_genome']


def test_generate_qc_data(case_data, report_api):
    # GIVEN data from an analysed case and an initialised report_api

    # WHEN generating_qc_data
    qc_data = report_api.generate_qc_data(case_data)

    # THEN certain metrics should have been calculated
    # today contains the today date
    assert qc_data['today']

    # customer is the customer in the in-data but niceified
    assert qc_data['customer']
    assert case_data['customer'] != qc_data['customer']

    # each sample has a property library_prep_method with a value
    for sample in qc_data['samples']:
        assert sample['library_prep_method']

    # each sample has a property sequencing_method with a value
    for sample in qc_data['samples']:
        assert sample['sequencing_method']

    # each sample has a property delivery_method with a value
    for sample in qc_data['samples']:
        assert sample['delivery_method']

    # each sample has a property project with a value that is the first word of the project
    #   property in the indata
    for sample in qc_data['samples']:
        assert ' ' not in sample['project']

    # each sample has a property processing_time with a value of the days between received_at and
    #   delivery_date
    for sample in qc_data['samples']:
        assert sample['processing_time']

    # the generated data has a property apptags with a value
    assert qc_data['apptags']

    # the generated data has a property accredited with a value
    assert qc_data['accredited'] is False
    #print(qc_data)
    #assert False


def test_render_qc_report(case_data, report_api):
    # GIVEN proper qc data from an analysis exist
    report_data = report_api.generate_qc_data(case_data)

    # WHEN rendering a report from that data
    rendered_report = ReportAPI.render_qc_report(report_data)

    # THEN a html report with certain data should have been rendered
    assert len(rendered_report) > 0
    print(rendered_report)
    assert False
