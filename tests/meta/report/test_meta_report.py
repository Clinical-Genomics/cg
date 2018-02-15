
from cg.meta.report.api import ReportAPI


def test_generate_qc_data(case_data, report_api):
    # GIVEN data from an analysed case and an report_api initialised


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


def test_render_qc_report(case_data):
    # GIVEN proper qc data from an analysis exist
    # WHEN rendering a report from that data
    # THEN a html report with certain data should have been rendered
    rendered_report = ReportAPI.render_qc_report(case_data)
    assert len(rendered_report) > 0
