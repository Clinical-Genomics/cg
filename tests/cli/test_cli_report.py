
from cg.store import Store
from cg.cli import report


def test_report(invoke_cli, disk_store: Store):
    # GIVEN an empty database

    # WHEN calling the report command
    db_uri = disk_store.uri
    result = invoke_cli(['--database', db_uri, 'report'])

    # THEN success
    assert result.exit_code == 0


def test_generate_qc_data(case_data, base_store):
    # GIVEN data from an analysed case

    # WHEN generating_qc_data
    qc_data = report.generate_qc_data(base_store, case_data)

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
        assert not sample['project'].contains(' ')

    # each sample has a property processing_time with a value of the days between received_at and
    #   delivery_date
    for sample in qc_data['samples']:
        assert sample['processing_time']

    # the generated data has a property apptags with a value
    assert qc_data['apptags']

    # the generated data has a property accredited with a value
    assert qc_data['accredited']


def test_render_qc_report(case_data):
    # GIVEN proper qc data from an analysis exist
    # WHEN rendering a report from that data
    # THEN a html report with certain data should have been rendered
    rendered_report = report.render_qc_report(case_data)
    assert len(rendered_report) > 0


def test_cli_report_qc(invoke_cli, case_data_path, disk_store: Store):
    # GIVEN an empty database

    # WHEN calling the report command
    db_uri = disk_store.uri
    result = invoke_cli(['--database', db_uri, 'report', 'qc', case_data_path])

    print(result.exception)
    print(result.output)
    print(result.runner)

    # THEN success
    assert result.exit_code == 0
